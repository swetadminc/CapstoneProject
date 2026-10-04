"""Render the narrated InvestigateIQ course-demo overview as a local MP4.

This is an animated guide to the implemented workflow, not a screen recording.
It uses Pillow for slides, Windows speech for narration, and local FFmpeg.
No customer data, external service, model key, or network connection is used.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import json
import math
import base64
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "investigateiq_walkthrough.mp4"
WIDTH, HEIGHT = 1280, 720
FFMPEG_FALLBACK = Path(r"C:\Program Files (x86)\Icecream Screen Recorder 7\ffmpeg.exe")
FONT_REGULAR = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")

SLIDES = [
    {
        "title": "InvestigateIQ",
        "narration": "Investigate IQ helps investigators review fictional anti money laundering alerts. AI drafts; people decide.",
        "subtitle": "AI drafts the report. A human makes the call.",
        "cards": [
            ("01", "Alert", "A fictional case enters the queue"),
            ("02", "Investigate", "Evidence and guidance support a draft"),
            ("03", "Decide", "An investigator records the reason"),
            ("04", "Follow up", "Compliance reviews escalations"),
        ],
        "note": "Purpose: make alert review evidence-linked and auditable. Fictional course prototype.",
    },
    {
        "title": "Start with the Case Queue",
        "narration": "Open the Case Queue and choose a fictional alert. These are not live bank transactions.",
        "subtitle": "Pick a preloaded alert that needs human review.",
        "cards": [
            ("1", "Scan", "See alert counts, severity and status"),
            ("2", "Filter", "Narrow the list to a case of interest"),
            ("3", "Open", "Move into the Investigation Workspace"),
        ],
        "note": "This is not live transaction monitoring; all alerts are fictional examples.",
    },
    {
        "title": "Investigate in six steps",
        "narration": "Six steps bring together the alert, customer, transactions, relationships, evidence, and a draft summary.",
        "subtitle": "Small specialist steps assemble the case context.",
        "cards": [
            ("01", "Alert triage", "What triggered the alert?"),
            ("02", "Customer / KYC", "Who is involved?"),
            ("03", "Transactions", "What moved and when?"),
            ("04", "Relationships", "Who is connected?"),
            ("05", "Evidence", "Which records and guidance help?"),
            ("06", "Summary", "Draft findings for review"),
        ],
        "note": "Cached replay supports the demo. Live AI drafting needs a configured model key.",
    },
    {
        "title": "Check the draft against evidence",
        "narration": "Review the draft against source records and guidance. Validation covers selected claims, not every sentence.",
        "subtitle": "The report is a starting point, not a verdict.",
        "cards": [
            ("A", "Records", "Inspect transactions, customer context and documents"),
            ("B", "Guidance", "Retrieve relevant synthetic playbook passages"),
            ("C", "Validation", "Check selected citations and numeric claims"),
        ],
        "note": "The validator checks selected claims; it does not guarantee every sentence is correct.",
    },
    {
        "title": "The investigator decides",
        "narration": "The investigator closes or escalates the case with a reason. Their decision is saved to the audit trail.",
        "subtitle": "AI assistance stops short of the final decision.",
        "cards": [
            ("1", "Review", "Read findings and ask evidence-linked questions"),
            ("2", "Decide", "Close or escalate with a required rationale"),
            ("3", "Audit", "Save who acted, when, and why"),
        ],
        "note": "A report draft and PDF support review; they are not automatic approvals.",
    },
    {
        "title": "Compliance follows up",
        "narration": "Escalated cases reach Compliance for review, return, or referral. The prototype does not file with regulators.",
        "subtitle": "Escalated cases move to a separate human queue.",
        "cards": [
            ("A", "Acknowledge", "Record that the case was reviewed"),
            ("B", "Return", "Ask the investigator for more information"),
            ("C", "Refer", "Record an onward referral decision"),
        ],
        "note": "A recorded referral is not a regulatory filing. This tool files nothing automatically.",
    },
    {
        "title": "Explore and explain",
        "narration": "Search, analytics, knowledge base, and rule settings support exploration. These are classroom prototype controls.",
        "subtitle": "Supporting screens make the prototype easier to inspect.",
        "cards": [
            ("S", "Global Search", "Find fictional customers, accounts and transactions"),
            ("A", "Analytics", "See descriptive alert and decision trends"),
            ("K", "Knowledge Base", "Inspect synthetic retrieval and document chunks"),
            ("R", "Rule Config", "Preview thresholds without regenerating alerts"),
        ],
        "note": "Admin gates are prototype controls, not production-grade access management.",
    },
    {
        "title": "Know the boundary",
        "narration": "The workflow uses fictional data. It is not connected to a real bank or regulator.",
        "subtitle": "What the course demonstration can — and cannot — show.",
        "cards": [
            ("OK", "Working flow", "Queue, evidence, draft, decision and audit"),
            ("OK", "Fictional data", "Safe examples for a classroom demonstration"),
            ("NO", "No bank link", "No connection to a real bank's systems"),
            ("NO", "No filing", "No automatic reporting to a regulator"),
        ],
        "note": "Indian regulatory applicability needs official review before real-world use.",
    },
    {
        "title": "Try the live workflow",
        "narration": "Try the live workflow: choose a case, inspect the evidence, and explain your decision.",
        "subtitle": "Case Queue → Investigation → Human Decision → Compliance",
        "cards": [
            ("1", "Choose a case", "Start with a preloaded fictional alert"),
            ("2", "Inspect the draft", "Check sources, findings and limitations"),
            ("3", "Explain the choice", "Record a human rationale and see the audit trail"),
        ],
        "note": "InvestigateIQ · Capstone Group 7 · Leadership with AI, IIT Bombay",
    },
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def wrapped_lines(draw: ImageDraw.ImageDraw, value: str, text_font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), trial, font=text_font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def render_slide(slide: dict, index: int, target: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), (9, 17, 32))
    draw = ImageDraw.Draw(image)
    # Branded but restrained: large readable text and a clear progress marker.
    draw.rounded_rectangle((42, 38, WIDTH - 42, HEIGHT - 38), radius=30,
                           fill=(18, 33, 57), outline=(44, 72, 112), width=2)
    draw.rounded_rectangle((79, 72, 312, 112), radius=19, fill=(43, 101, 193))
    draw.text((100, 77), "INVESTIGATEIQ", font=font(19, True), fill=(255, 255, 255))
    draw.text((WIDTH - 184, 82), f"{index:02d} / {len(SLIDES):02d}", font=font(19, True), fill=(159, 188, 227))
    title_size = 54 if len(slide["title"]) < 31 else 46
    draw.text((80, 142), slide["title"], font=font(title_size, True), fill=(245, 249, 255))
    draw.text((82, 218), slide["subtitle"], font=font(25), fill=(190, 216, 248))

    cards = slide["cards"]
    columns = 3 if len(cards) in (3, 6) else 4
    rows = 2 if len(cards) == 6 else 1
    gap = 18
    usable_width = WIDTH - 160
    card_width = (usable_width - gap * (columns - 1)) // columns
    card_height = 142 if rows == 2 else 216
    top = 286
    for card_index, (marker, heading, detail) in enumerate(cards):
        col, row = card_index % columns, card_index // columns
        x = 80 + col * (card_width + gap)
        y = top + row * (card_height + gap)
        draw.rounded_rectangle((x, y, x + card_width, y + card_height), radius=20,
                               fill=(28, 49, 79), outline=(73, 112, 165), width=2)
        draw.rounded_rectangle((x + 18, y + 16, x + 66, y + 58), radius=12, fill=(43, 101, 193))
        marker_font = font(19, True)
        marker_box = draw.textbbox((0, 0), marker, font=marker_font)
        draw.text((x + 42 - (marker_box[2] - marker_box[0]) / 2, y + 22), marker,
                  font=marker_font, fill=(255, 255, 255))
        heading_font = font(22 if rows == 2 else (24 if columns == 3 else 21), True)
        heading_lines = wrapped_lines(draw, heading, heading_font, card_width - 36)
        title_y = y + (63 if rows == 2 else 70)
        for line in heading_lines[:2]:
            draw.text((x + 18, title_y), line, font=heading_font, fill=(248, 251, 255))
            title_y += 25 if rows == 2 else 28
        detail_font = font(16 if rows == 2 else (18 if columns == 3 else 17))
        for line in wrapped_lines(draw, detail, detail_font, card_width - 36)[:3]:
            draw.text((x + 18, title_y + (6 if rows == 2 else 9)), line,
                      font=detail_font, fill=(188, 207, 233))
            title_y += 21 if rows == 2 else 25

    draw.line((80, 626, WIDTH - 80, 626), fill=(69, 99, 138), width=2)
    note_font = font(17)
    for line_index, line in enumerate(wrapped_lines(draw, slide["note"], note_font, WIDTH - 170)[:2]):
        draw.text((82, 642 + line_index * 21), line, font=note_font, fill=(164, 188, 218))
    # The available local FFmpeg build decodes BMP but not PNG.
    image.save(target, format="BMP")


def find_ffmpeg() -> str:
    if FFMPEG_FALLBACK.exists():
        return str(FFMPEG_FALLBACK)
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise RuntimeError("FFmpeg is required to render the walkthrough MP4")


def synthesize_narration(folder: Path, slides: list[dict] | None = None) -> list[Path]:
    """Generate one local WAV per scene with an installed English female voice."""
    slides = SLIDES if slides is None else slides
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise RuntimeError("Windows PowerShell speech synthesis is required for narration")
    tracks = [folder / f"narration_{index:02d}.wav" for index in range(1, len(slides) + 1)]
    manifest = folder / "narration.json"
    manifest.write_text(
        json.dumps([{"path": str(path), "text": slide["narration"]}
                    for path, slide in zip(tracks, slides)], ensure_ascii=False),
        encoding="utf-8",
    )
    manifest_path = str(manifest).replace("'", "''")
    script = f"""
Add-Type -AssemblyName System.Speech
$entries = Get-Content -LiteralPath '{manifest_path}' -Raw | ConvertFrom-Json
$synth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {{
    $voice = $synth.GetInstalledVoices() | Where-Object {{
        $_.VoiceInfo.Culture.Name -eq 'en-IN' -and $_.VoiceInfo.Gender -eq 'Female'
    }} | Select-Object -First 1
    if (-not $voice) {{
        $voice = $synth.GetInstalledVoices() | Where-Object {{
            $_.VoiceInfo.Culture.Name -like 'en-*' -and $_.VoiceInfo.Gender -eq 'Female'
        }} | Select-Object -First 1
    }}
    if (-not $voice) {{ throw 'No installed English female speech voice was found.' }}
    $synth.SelectVoice($voice.VoiceInfo.Name)
    Write-Output ('Narration voice: ' + $voice.VoiceInfo.Name + ' (' + $voice.VoiceInfo.Gender + ')')
    $synth.Rate = 0
    foreach ($entry in $entries) {{
        $synth.SetOutputToWaveFile($entry.path)
        $synth.Speak($entry.text)
        $synth.SetOutputToNull()
    }}
}} finally {{ $synth.Dispose() }}
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    result = subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                            capture_output=True, text=True)
    if result.returncode:
        # Some clean Windows build agents have System.Speech installed but no
        # registered voice. Fall back to the installed Edge TTS CLI so a
        # narrated walkthrough can still be rebuilt from the same storyboard.
        edge_tts = shutil.which("edge-tts")
        if not edge_tts:
            raise RuntimeError(f"Windows speech synthesis failed: {result.stderr.strip()}")
        ffmpeg = find_ffmpeg()
        print("Windows speech voices unavailable; using Edge TTS fallback (en-US-JennyNeural).")
        entries = json.loads(manifest.read_text(encoding="utf-8"))
        for entry in entries:
            wav_path = Path(entry["path"])
            mp3_path = wav_path.with_suffix(".mp3")
            edge_result = subprocess.run(
                [edge_tts, "--voice", "en-US-JennyNeural", "--text", entry["text"],
                 "--write-media", str(mp3_path)],
                capture_output=True, text=True,
            )
            if edge_result.returncode or not mp3_path.is_file() or mp3_path.stat().st_size < 1024:
                raise RuntimeError(f"Edge TTS narration failed: {edge_result.stderr.strip()}")
            convert = subprocess.run(
                [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp3_path),
                 "-ac", "1", "-ar", "22050", str(wav_path)],
                capture_output=True, text=True,
            )
            mp3_path.unlink(missing_ok=True)
            if convert.returncode or not wav_path.is_file():
                raise RuntimeError(f"Could not convert Edge TTS narration: {convert.stderr.strip()}")
    elif result.stdout.strip():
        print(result.stdout.strip())
    for track in tracks:
        if not track.is_file() or track.stat().st_size < 1024:
            raise RuntimeError(f"Narration was not produced: {track.name}")
    return tracks


def join_narration(tracks: list[Path], target: Path) -> list[int]:
    """Pad each spoken scene so speech and visual scene changes stay aligned."""
    durations = []
    parameters = None
    with wave.open(str(target), "wb") as output:
        for track in tracks:
            with wave.open(str(track), "rb") as source:
                if parameters is None:
                    parameters = source.getparams()
                    output.setparams(parameters)
                elif (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (
                    parameters.nchannels, parameters.sampwidth, parameters.framerate
                ):
                    raise RuntimeError("Narration WAV formats do not match")
                frame_count = source.getnframes()
                duration = max(8, math.ceil(frame_count / source.getframerate() + 1.5))
                output.writeframes(source.readframes(frame_count))
                silence_frames = duration * source.getframerate() - frame_count
                output.writeframes(b"\x00" * silence_frames * source.getnchannels() * source.getsampwidth())
                durations.append(duration)
    return durations


def build() -> Path:
    with tempfile.TemporaryDirectory(prefix="investigateiq-video-") as folder:
        frame_dir = Path(folder)
        frames = []
        for index, slide in enumerate(SLIDES, start=1):
            frame = frame_dir / f"slide_{index:02d}.bmp"
            render_slide(slide, index, frame)
            frames.append(frame)

        narration = frame_dir / "narration_all.wav"
        durations = join_narration(synthesize_narration(frame_dir), narration)

        # Scene lengths follow speech, with reading time after each sentence.
        command = [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"]
        for frame, duration in zip(frames, durations):
            command += ["-loop", "1", "-framerate", "24", "-t", str(duration), "-i", str(frame)]
        command += ["-i", str(narration)]
        filters = []
        for index, duration in enumerate(durations):
            intro_fade = "fade=t=in:st=0:d=0.3," if index else ""
            filters.append(
                f"[{index}:v]fps=24,format=yuv420p,{intro_fade}"
                f"fade=t=out:st={duration - 0.3}:d=0.3[v{index}]"
            )
        filters.append("".join(f"[v{index}]" for index in range(len(frames)))
                       + f"concat=n={len(frames)}:v=1:a=0[out]")
        command += ["-filter_complex", ";".join(filters), "-map", "[out]", "-map", f"{len(frames)}:a:0",
                    "-c:v", "libopenh264", "-b:v", "1200k", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", str(OUTPUT)]
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(command, check=True)
    return OUTPUT


if __name__ == "__main__":
    print(build())

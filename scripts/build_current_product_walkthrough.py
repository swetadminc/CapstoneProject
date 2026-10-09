"""Render the current-product InvestigateIQ walkthrough.

Every scene comes from a fresh, native 1280x720 capture made by
``capture_current_walkthrough.js``.  The renderer deliberately never scales a
capture beyond that canvas, and only draws a pointer where a reviewed target is
specified.  It does not reuse any screenshot from the retired walkthrough.
"""

from __future__ import annotations

import math
import os
import re
import subprocess
import tempfile
import textwrap
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    from .build_walkthrough import find_ffmpeg, join_narration, synthesize_narration
except ImportError:
    from build_walkthrough import find_ffmpeg, join_narration, synthesize_narration


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "assets" / "walkthrough_screens"
OUTPUT = ROOT / "assets" / "investigateiq_walkthrough.mp4"
POSTER = ROOT / "assets" / "investigateiq_walkthrough_poster.png"
SUBTITLES = ROOT / "assets" / "investigateiq_walkthrough.vtt"
WIDTH, HEIGHT, FPS = 1280, 720, 8
FONT = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")
TITLE = "InvestigateIQ: Current Product Walkthrough"

# ``target`` points to the reviewed control being discussed.  It is omitted
# when the narration is explaining the whole visible screen, preventing the
# old video's problem of a cursor pointing into unrelated whitespace.
SCENES = [
    ("2026_home_guest.png", "Start on the current Home screen. A display name and one of the four workflow labels start the fictional demo workspace. The field attributes later human actions; it is not authentication, and choosing a role does not grant real-world authority. We will use the reordered left navigation to visit every current product page.", None),
    ("2026_case_queue_top.png", "Case Queue is the operational starting point. Its summary cards separate total alerts, open work, source-closed labels, escalation counts, and High severity. These are stored fictional workflow labels, not proof that money is lawful or unlawful.", None),
    ("2026_case_queue_table.png", "Scroll slowly to the filters and table. Search customer name narrows the queue; the row then exposes case, customer, alert type, severity, current status, recorded rule labels, and an action to inspect the case. A status and an action have distinct meanings.", (1054, 323)),
    ("2026_case_queue_filtered.png", "The filtered queue demonstrates the same review flow with a smaller result set. An open case can be investigated. A closed or reviewed case instead retains an Evidence path, so the user can inspect the support without treating the label as an invitation to change a completed human decision.", None),
    ("2026_workspace_current_report.png", "Investigation Workspace begins with a selected case and a repeatable saved-report mode. Run investigation replays a historical snapshot or the calculated mode can evaluate the current fictional rows. Neither mode records a human decision by itself.", (453, 438)),
    ("2026_workspace_confidence.png", "After the report is built, Evidence confidence appears prominently. Here the support score is 45 out of 100, with Low support and four known limitations. This is a transparent evidence-coverage check, not a probability of crime, money laundering, or the recommended outcome.", (545, 124)),
    ("2026_workspace_findings.png", "Continue down the report to the case context and Evidence and Findings. The screen preserves its source-data warning and identifies review-window facts. It makes the limitation visible before any person is asked to make a decision.", None),
    ("2026_evidence_case_records.png", "Evidence and RAG is where citations become inspectable records. Its compact flow describes choosing a case, reading exact source text and chunks, checking coverage, and testing retrieval. This is the evidence workspace, not a claim that a cited record establishes wrongdoing.", None),
    ("2026_evidence_case_records_detail.png", "Scroll into Case records. The selected case shows its indexed passages, identity-record limitations, original-file count, and unmatched counterparties. The page explicitly distinguishes a generated record or dataset field from independently verified evidence.", None),
    ("2026_evidence_copilot_open.png", "The floating InvestigateIQ Copilot opens on the same page, keeping the selected case visible. Because this capture is a non-submitting demonstration, it asks the viewer to enter a workspace before asking a question. The Copilot is a bounded explanation tool; it never selects or submits the human action.", None),
    ("2026_evidence_rule_lab.png", "Rule Lab is a separate evidence tab. It explains the alert-rule metadata and preview boundary, so a red or matched condition is read as a review signal—not a verdict and not a replacement for source evidence.", None),
    ("2026_evidence_fictional_intake.png", "Fictional Intake shows the separate calculated packet workflow. This deliberately generated example is visibly different from an imported alert: its rows, source text, and evidence gaps are labeled as fictional rather than presented as original banking records.", None),
    ("2026_evidence_source_chunks.png", "Source and chunks lets an investigator open the source document behind a cited guidance passage. The document and its chunks are shown separately, which makes the retrieval path reviewable rather than hiding it inside a generated answer.", None),
    ("2026_evidence_source_chunks_detail.png", "As we continue to scroll, exact chunks and their metadata stay connected to their source. A chunk is a searchable excerpt with an identifier and scope. It is useful for traceability, but its presence does not independently establish a customer fact.", None),
    ("2026_evidence_search_index.png", "Search the index makes the retrieval method visible. It searches the stored fictional sources and case passages; results are leads for inspection, not unverified answers presented as facts.", None),
    ("2026_evidence_search_index_detail.png", "The detailed result area lets the investigator compare result text, scope, and source identifier before relying on a passage. This is why the product shows the evidence boundary alongside the result.", None),
    ("2026_evidence_method_code.png", "Method and code documents how records, chunks, retrieval, and checks connect. It is included so a reviewer can understand the product’s method rather than treating the UI as a black box.", None),
    ("2026_evidence_method_code_detail.png", "Continue through the implementation notes slowly. The documented method is deliberately limited: it can retrieve and trace supplied fictional material, but cannot verify outside-bank facts or make a legal finding.", None),
    ("2026_compliance_queue.png", "Compliance Queue contains cases an investigator has explicitly escalated. It is a second human-review step, separate from the investigator’s decision panel. Nothing on this screen files a report with a regulator.", None),
    ("2026_compliance_queue_detail.png", "The Compliance outcomes are distinguished in the queue and audit history: acknowledge means reviewed with no further action; return sends the case back for more information; referred onward records that a referral was made by a human. The labels preserve the next state of the case.", None),
    ("2026_analytics.png", "Analytics starts with descriptive summaries of the fictional dataset. Read each title and axis as a count or share of stored labels—not as a prediction, fraud score, productivity rating, or probability of crime.", None),
    ("2026_analytics_charts.png", "Here the graphs are fully in view. Alerts by current status uses number of cases on the horizontal axis. High-severity share by typology uses percentage on the horizontal axis. The explanatory text below each graph states the unit and what it does not measure.", None),
    ("2026_analytics_lower_charts.png", "As the page scrolls further, the remaining charts show stored records over time and recorded human actions. A monthly alert line counts fictional records for each time bucket. Human-action charts count saved actions; they do not measure final outcomes or staff performance.", None),
    ("2026_global_search.png", "Global Search is read-only. A user can look up a fictional customer, account, transaction reference, or case identifier, then use a matching record to regain context in Investigation Workspace. Search locates records; it does not reach a conclusion.", None),
    ("2026_project_team.png", "Project and Team names the confirmed roster and makes the product’s planning responsibilities visible by person. This section uses names only, without email addresses, and does not imply production permissions.", None),
    ("2026_project_team_roles.png", "The open role guide explains the four workflow roles. The Investigator reviews evidence and records an accountable action; the Team Lead coordinates; the Compliance Officer conducts second review; the Admin maintains fictional guidance and rules after a separate passcode gate. Labels do not authenticate a user.", None),
    ("2026_admin_knowledge_locked.png", "Admin Knowledge Base is intentionally shown in its locked state. The video does not expose, store, or automate a passcode. The boundary is visible: protected source-inspection tools require a separate authorized unlock.", None),
    ("2026_admin_rules_locked.png", "Admin Rule Config has the same protected boundary. This concludes the current product tour: InvestigateIQ shows the evidence trail, the retrieval method, the score’s limitation, and the human workflow. It does not make the final decision or file anything automatically.", None),
]


def face(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size)


def fit(image: Image.Image) -> Image.Image:
    """Letterbox a non-native image instead of ever stretching it."""
    image = image.convert("RGB")
    if image.size == (WIDTH, HEIGHT):
        return image
    scale = min(WIDTH / image.width, HEIGHT / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#eef4fc")
    canvas.paste(resized, ((WIDTH - resized.width) // 2, (HEIGHT - resized.height) // 2))
    return canvas


def pointer(draw: ImageDraw.ImageDraw, target: tuple[int, int], progress: float) -> None:
    """Draw a small pointer whose tip lands exactly on its reviewed target."""
    tx, ty = target
    sx, sy = tx + (-64 if tx > WIDTH // 2 else 64), ty + (-52 if ty > HEIGHT // 2 else 52)
    # Arrive only during the opening seconds; avoid a constantly moving cursor.
    arrival = min(1.0, progress * 4.0)
    x, y = sx + (tx - sx) * arrival, sy + (ty - sy) * arrival
    draw.line((sx, sy, x, y), fill="#075dcb", width=4)
    draw.ellipse((tx - 13, ty - 13, tx + 13, ty + 13), outline="#075dcb", width=4)
    draw.ellipse((tx - 7, ty - 7, tx + 7, ty + 7), fill="#ffffff", outline="#075dcb", width=2)
    angle = math.atan2(ty - sy, tx - sx)
    tip = (x, y)
    left = (x - 18 * math.cos(angle - .55), y - 18 * math.sin(angle - .55))
    right = (x - 18 * math.cos(angle + .55), y - 18 * math.sin(angle + .55))
    draw.polygon([tip, left, right], fill="#075dcb")


def frame(base: Image.Image, target: tuple[int, int] | None, progress: float) -> Image.Image:
    image = base.copy()
    if target:
        pointer(ImageDraw.Draw(image), target, progress)
    return image


def timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remaining = divmod(milliseconds, 3_600_000)
    minutes, remaining = divmod(remaining, 60_000)
    whole, millis = divmod(remaining, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole:02d}.{millis:03d}"


def write_vtt(tracks: list[Path], durations: list[int], target: Path) -> None:
    lines = ["WEBVTT", ""]
    start = 0.0
    number = 1
    for (_, narration, _), track, duration in zip(SCENES, tracks, durations):
        with wave.open(str(track), "rb") as stream:
            spoken = stream.getnframes() / stream.getframerate()
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", narration) if item.strip()]
        words = max(1, sum(len(item.split()) for item in sentences))
        running = 0
        for sentence in sentences:
            cue_start = start + .08 + spoken * running / words
            running += len(sentence.split())
            cue_end = start + .08 + spoken * running / words
            lines.extend([str(number), f"{timestamp(cue_start)} --> {timestamp(cue_end)}", textwrap.fill(sentence, 74), ""])
            number += 1
        start += duration
    target.write_text("\n".join(lines), encoding="utf-8")


def poster(base: Image.Image) -> Image.Image:
    image = base.convert("RGBA")
    shade = Image.new("RGBA", image.size, (7, 23, 47, 178))
    image = Image.alpha_composite(image, shade)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((92, 238, 1188, 496), radius=25, fill=(10, 35, 69, 235), outline=(116, 177, 255, 255), width=3)
    draw.text((142, 286), "INVESTIGATEIQ", font=face(30, True), fill="#a9d0ff")
    draw.text((142, 348), "Current product walkthrough", font=face(47, True), fill="white")
    draw.text((142, 420), "Evidence trail · transparent confidence · human decisions", font=face(24), fill="#d5e7ff")
    return image.convert("RGB")


def build() -> Path:
    missing = [screen for screen, _, _ in SCENES if not (SCREENS / screen).is_file()]
    if missing:
        raise FileNotFoundError("Fresh capture missing: " + ", ".join(missing))
    images = [fit(Image.open(SCREENS / screen)) for screen, _, _ in SCENES]
    poster(images[1]).save(POSTER)
    with tempfile.TemporaryDirectory(prefix="investigateiq-current-video-") as temp_name:
        temp = Path(temp_name)
        tracks = synthesize_narration(temp, [{"narration": narration} for _, narration, _ in SCENES])
        narration_file = temp / "narration.wav"
        durations = join_narration(tracks, narration_file)
        pending_video = OUTPUT.with_suffix(".rendering.mp4")
        pending_vtt = SUBTITLES.with_suffix(".rendering.vtt")
        write_vtt(tracks, durations, pending_vtt)
        command = [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pixel_format", "rgb24",
                   "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS), "-i", "-", "-i", str(narration_file),
                   "-c:v", "libopenh264", "-b:v", "900k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "80k",
                   "-metadata", f"title={TITLE}", "-movflags", "+faststart", str(pending_video)]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            assert process.stdin is not None
            for image, (_, _, target), duration in zip(images, SCENES, durations):
                for number in range(duration * FPS):
                    process.stdin.write(frame(image, target, number / max(1, duration * FPS)).tobytes())
            process.stdin.close()
            errors = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            if process.wait() != 0:
                raise RuntimeError(f"FFmpeg video render failed: {errors}")
            os.replace(pending_video, OUTPUT)
            os.replace(pending_vtt, SUBTITLES)
        finally:
            if process.poll() is None:
                process.kill()
    return OUTPUT


if __name__ == "__main__":
    print(build())

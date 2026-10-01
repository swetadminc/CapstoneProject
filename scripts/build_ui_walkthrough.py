"""Build a narrated, animated guide from captured public app screens.

The captured screens live in assets/walkthrough_screens. Cursor movement,
click rings, and page transitions are animated explanations, not a claim that
this MP4 is an unedited screen recording. All customer data is fictional.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    from .build_walkthrough import find_ffmpeg, join_narration, synthesize_narration
except ImportError:  # Direct invocation: python scripts/build_ui_walkthrough.py
    from build_walkthrough import find_ffmpeg, join_narration, synthesize_narration


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "assets" / "walkthrough_screens"
OUTPUT = ROOT / "assets" / "investigateiq_walkthrough.mp4"
POSTER = ROOT / "assets" / "investigateiq_walkthrough_poster.png"
WIDTH, HEIGHT, FPS = 1280, 720, 12
FONT = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")

# Every screenshot below came from the deployed public application. Cursor
# movement is explanatory animation, not footage of an unedited interaction.
# The CASE-041 decision form is shown before submission; no human decision is
# attributed to the fictional display identity by this video.
SCENES = [
    {"screen": "01_home_guest.png", "title": "InvestigateIQ Product Walkthrough",
     "narration": "Welcome to Investigate IQ. This product helps an investigator review a monitoring alert, trace an evidence-linked draft, and own the final decision. All case data in this walkthrough is fictional.",
     "target": None},
    {"screen": "02_public_identity.png", "title": "Enter the Workspace",
     "narration": "On Home, enter a display name and choose a workflow role. Actions are attributed to that name. This course environment uses display identity, not bank-grade authentication.",
     "target": (1010, 385)},
    {"screen": "03_public_home_ready.png", "title": "Follow the Product Journey",
     "narration": "The landing page explains the journey: an alert arrives, the copilot prepares a draft, a human reviews it, and Compliance receives only escalated cases. The sidebar opens every screen.",
     "target": (115, 160)},
    {"screen": "04_public_queue.png", "title": "Case Queue: Find an Alert",
     "narration": "The Case Queue lists fictional monitoring alerts with severity, status, and trigger metadata. Filters help an investigator choose a case. It is not a live bank transaction monitor.",
     "target": (710, 465)},
    {"screen": "05_public_case_filtered.png", "title": "Open CASE-041",
     "narration": "Search for Coastal Wholesale Traders. Case zero four one shows repeated near-threshold cash deposits. We open it to examine the evidence, rather than treating the alert itself as proof.",
     "target": (1153, 512)},
    {"screen": "06_public_investigation_start.png", "title": "Investigation Workspace",
     "narration": "Choose the case and run its saved investigation. Cached mode replays an existing AI-generated report with no new model call. Live analysis is a separate option when a model connection is configured.",
     "target": (510, 555)},
    {"screen": "07_public_case_summary.png", "title": "Review the Draft Summary",
     "narration": "The report shows a six-transaction review window, a baseline of three hundred ninety five thousand rupees, and a trigger-to-baseline ratio of two point five. These are case facts to verify, not a verdict.",
     "target": (684, 239)},
    {"screen": "08_public_evidence.png", "title": "Check Cited Transactions",
     "narration": "Here the draft flags a deposit cluster and missing business-rationale documentation. Transaction IDs connect the statement to source records. Selected validation checks passed, but the investigator must still inspect the records.",
     "target": (595, 402)},
    {"screen": "09_public_copilot_answer.png", "title": "Ask the Copilot",
     "narration": "Ask what supports the concern. On this public site, the configured live model responds and cites transaction and playbook IDs. These references still need human checking. Without a model connection, the app offers limited saved-evidence question answering instead.",
     "target": (1015, 357), "caption_top": True},
    {"screen": "10_public_rag_overview.png", "title": "Evidence and RAG",
     "narration": "The Evidence and RAG page exposes the retrieval pipeline. It holds twenty four synthetic source documents and fifty seven chunks. It shows provenance, not proof that every generated sentence is correct.",
     "target": (149, 329)},
    {"screen": "10b_public_rag_source.png", "title": "Read the Cited Source",
     "narration": "The cited structuring playbook is visible as an original source document. It asks the reviewer to list each transaction and calculate the combined amount before judging whether the pattern deserves further scrutiny.",
     "target": (802, 310)},
    {"screen": "11_public_rag_chunks.png", "title": "See How the Source Is Chunked",
     "narration": "The database builder creates a metadata chunk from the title and criteria, then splits the body at sentence endings and groups two sentences per body chunk. These small passages are easier to inspect.",
     "target": (790, 464)},
    {"screen": "12_public_rag_retrieval.png", "title": "Try Keyword Retrieval",
     "narration": "Search for structuring cash deposits. SQLite FTS five finds matching chunks and B M twenty five ranks them. This is lexical retrieval, not vector or semantic search; the displayed result must still be read in context.",
     "target": (789, 332)},
    {"screen": "14_public_human_decision.png", "title": "The Investigator Decides",
     "narration": "The product offers close, request more information, or escalate to Compliance. The AI cannot choose or submit a decision. A rationale is required, and a submitted action is recorded in the audit log.",
     "target": (542, 334), "caption_top": True},
    {"screen": "15_public_reasoned_decision.png", "title": "Example: Request More Information",
     "narration": "For this case, a careful next step is to request the business explanation and counterparty agreements. The form shows that reasoning, but this walkthrough does not submit the decision. Missing evidence prevents a confident final conclusion.",
     "target": (750, 348)},
    {"screen": "16_public_compliance_queue.png", "title": "Compliance Queue",
     "narration": "If an investigator later escalates a case, it enters this separate Compliance Queue for a second human review. At recording time no cases awaited review. The app does not file a report with a regulator.",
     "target": (130, 230)},
    {"screen": "17_public_analytics.png", "title": "Analytics",
     "narration": "Analytics summarizes fictional alerts by severity, typology, status, and time. It helps a team see workload patterns. These charts do not establish model accuracy or real-world crime-detection performance.",
     "target": (140, 261)},
    {"screen": "18_public_global_search.png", "title": "Global Search",
     "narration": "Global Search finds a customer, case, account, or transaction across the synthetic dataset. Searching Coastal shows the same case plus linked records, so investigators can move between an alert and its context.",
     "target": (785, 501)},
    {"screen": "19_public_team.png", "title": "Project and Team",
     "narration": "The Project and Team screen names Capstone Group Seven and shows proposed responsibilities. The group should confirm each name and role before academic submission. The product name is Investigate IQ.",
     "target": (140, 126)},
    {"screen": "20_public_admin_knowledge.png", "title": "Admin: Knowledge Base",
     "narration": "The Knowledge Base inspector is an admin view of fictional playbooks and retrieval. The public Evidence and RAG screen gives a read-only explanation without needing the admin passcode.",
     "target": (163, 366)},
    {"screen": "21_public_admin_rules.png", "title": "Admin: Rule Configuration",
     "narration": "The Rule Configuration screen previews changes to two illustrative alert thresholds and records saves in the audit trail. It does not regenerate existing alerts or replace a bank monitoring engine. The final decision remains human.",
     "target": (155, 399)},
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size)


def wrap(draw: ImageDraw.ImageDraw, value: str, face: ImageFont.FreeTypeFont, limit: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in value.split():
        trial = f"{line} {word}".strip()
        if line and draw.textbbox((0, 0), trial, font=face)[2] > limit:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def poster_image(screen: Image.Image) -> Image.Image:
    image = screen.convert("RGBA")
    shade = Image.new("RGBA", image.size, (7, 19, 39, 192))
    image = Image.alpha_composite(image, shade)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((112, 190, 1168, 532), radius=26,
                           fill=(15, 32, 59, 244), outline=(113, 159, 227, 255), width=3)
    draw.text((163, 225), "INVESTIGATEIQ", font=font(27, True), fill="#9EC6FF")
    draw.text((163, 285), "Follow a Case, Step by Step", font=font(48, True), fill="white")
    draw.text((166, 366), "Real app screens  |  narrated guide  |  fictional data", font=font(25), fill="#D8E7FF")
    draw.ellipse((962, 302, 1060, 400), fill="#2E63BF", outline="#A6CAFF", width=3)
    draw.polygon([(1000, 323), (1000, 379), (1041, 351)], fill="white")
    draw.text((166, 464), "AI drafts. People decide. No regulatory filing.", font=font(22), fill="#AFCAEC")
    return image.convert("RGB")


def draw_cursor(draw: ImageDraw.ImageDraw, target: tuple[int, int], progress: float) -> None:
    tx, ty = target
    start_x, start_y = max(300, tx - 190), max(76, ty - 120)
    eased = 1 - (1 - min(1, progress / 0.72)) ** 3
    x = round(start_x + (tx - start_x) * eased)
    y = round(start_y + (ty - start_y) * eased)
    if progress > 0.68:
        phase = (progress - 0.68) / 0.32
        radius = round(13 + 34 * phase)
        alpha_color = "#2E63BF" if phase < 0.7 else "#8CB7F2"
        draw.ellipse((tx-radius, ty-radius, tx+radius, ty+radius), outline=alpha_color, width=4)
        draw.ellipse((tx-7, ty-7, tx+7, ty+7), outline="#2E63BF", width=3)
    points = [(x, y), (x + 3, y + 34), (x + 11, y + 24), (x + 21, y + 42),
              (x + 30, y + 37), (x + 19, y + 20), (x + 32, y + 19)]
    draw.polygon(points, fill="white")
    draw.line(points + [points[0]], fill="#15345F", width=4, joint="curve")


def render_frame(scene: dict, scene_index: int, elapsed: float, duration: int,
                 base: Image.Image) -> Image.Image:
    progress = min(1.0, elapsed / duration)
    if scene_index == 0:
        image = poster_image(base)
        draw = ImageDraw.Draw(image)
        draw_cursor(draw, (1007, 350), min(1.0, progress * 1.5))
        draw.rounded_rectangle((160, 497, 1118, 504), radius=4, fill="#3E5E89")
        draw.rounded_rectangle((160, 497, 160 + round(958 * progress), 504),
                               radius=4, fill="#8AC4FF")
        return image
    # A slow camera move plus a travelling cursor makes the navigation
    # sequence legible instead of presenting motionless screenshots.
    scale = 1 + 0.025 * progress
    w, h = round(WIDTH * scale), round(HEIGHT * scale)
    enlarged = base.resize((w, h), Image.Resampling.BICUBIC)
    target = scene["target"] or (WIDTH // 2, HEIGHT // 2)
    left = round((w - WIDTH) * target[0] / WIDTH)
    top = round((h - HEIGHT) * target[1] / HEIGHT)
    image = enlarged.crop((left, top, left + WIDTH, top + HEIGHT)).convert("RGB")
    draw = ImageDraw.Draw(image)
    bar_top = 67 if scene.get("caption_top") else 559
    draw.rounded_rectangle((315, bar_top, 1254, bar_top + 143), radius=15,
                           fill="#102640", outline="#7BA8E7", width=2)
    draw.text((341, bar_top + 15), f"{scene_index:02d}  {scene['title']}",
              font=font(25, True), fill="#FFFFFF")
    for line_no, line in enumerate(wrap(draw, scene["narration"], font(20), 865)[:3]):
        draw.text((342, bar_top + 53 + line_no * 24), line, font=font(20), fill="#D7E8FF")
    draw.rounded_rectangle((340, bar_top + 125, 1228, bar_top + 130), radius=3, fill="#3E5E89")
    draw.rounded_rectangle((340, bar_top + 125, 340 + round(888 * progress), bar_top + 130),
                           radius=3, fill="#8AC4FF")
    adjusted = (round(target[0] * scale - left), round(target[1] * scale - top))
    draw_cursor(draw, adjusted, progress)
    return image


def build() -> tuple[Path, Path]:
    missing = [scene["screen"] for scene in SCENES if not (SCREENS / scene["screen"]).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing captured app screens: {', '.join(missing)}")
    screen_images = [Image.open(SCREENS / scene["screen"]).convert("RGB").resize((WIDTH, HEIGHT))
                     for scene in SCENES]
    POSTER.parent.mkdir(parents=True, exist_ok=True)
    poster_image(screen_images[0]).save(POSTER)
    with tempfile.TemporaryDirectory(prefix="investigateiq-ui-video-") as temp:
        folder = Path(temp)
        narration = folder / "narration_all.wav"
        durations = join_narration(synthesize_narration(folder, SCENES), narration)
        pending_output = OUTPUT.with_suffix(".rendering.mp4")
        command = [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                   "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
                   "-framerate", str(FPS), "-i", "-", "-i", str(narration),
                   "-c:v", "libopenh264", "-b:v", "2200k", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(pending_output)]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            assert process.stdin is not None
            for index, (scene, duration, base) in enumerate(zip(SCENES, durations, screen_images)):
                for frame_number in range(duration * FPS):
                    image = render_frame(scene, index, frame_number / FPS, duration, base)
                    process.stdin.write(image.tobytes())
            process.stdin.close()
            error = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            if process.wait() != 0:
                raise RuntimeError(f"FFmpeg could not render the guided video: {error}")
            os.replace(pending_output, OUTPUT)
        finally:
            if process.poll() is None:
                process.kill()
    return OUTPUT, POSTER


if __name__ == "__main__":
    print(build())

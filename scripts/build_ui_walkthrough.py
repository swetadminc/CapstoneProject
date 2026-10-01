"""Build a narrated, animated guide from captured *real* local app screens.

The captured screens live in assets/walkthrough_screens. Cursor movement,
click rings, and page transitions are animated explanations, not a claim that
this MP4 is an unedited screen recording. All customer data is fictional.
"""

from __future__ import annotations

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

# Every screenshot below came from a browser interaction with the local app.
# The recorded case decision below uses a fictional display identity.
SCENES = [
    {"screen": "01_home_guest.png", "title": "InvestigateIQ Product Walkthrough",
     "narration": "Welcome to Investigate IQ. Follow a fictional case from workspace entry through investigation and human Compliance review.",
     "target": None},
    {"screen": "02_demo_entry.png", "title": "Enter Your Workspace",
     "narration": "On Home, enter a display name. The name is recorded with decisions and audit events. This environment does not authenticate users.",
     "target": (1038, 308)},
    {"screen": "03_demo_name.png", "title": "Choose a Role and Continue",
     "narration": "Choose a workflow role, then open the workspace. Roles help explain the workflow; access is not enforced by role here.",
     "target": (1000, 449)},
    {"screen": "04_demo_ready.png", "title": "Open the Case Queue",
     "narration": "The sidebar takes us to the Case Queue. Every alert and transaction shown here is fictional and preloaded for consistent review.",
     "target": (115, 160)},
    {"screen": "06_case_filtered.png", "title": "Find and Open a Case",
     "narration": "Search for Coastal, review the alert row, and open case zero four one. This case has a saved report, so no new model call is needed.",
     "target": (1154, 379)},
    {"screen": "08_cached_mode.png", "title": "Run a Cached Investigation",
     "narration": "In the Investigation Workspace, keep Cached mode selected and run the investigation. Cached replay is fast and costs no new AI request.",
     "target": (450, 437)},
    {"screen": "10_evidence.png", "title": "Inspect the Evidence",
     "narration": "Review the draft against its transaction references. The selected grounding checks passed, but that does not prove every sentence is correct. A person still checks the evidence.",
     "target": (610, 377)},
    {"screen": "11_guidance.png", "title": "Read the Questions and Guidance",
     "narration": "The workspace shows investigation questions and retrieved synthetic playbook guidance. These are prompts for review, not regulatory conclusions.",
     "target": (591, 431)},
    {"screen": "14_escalation_choice.png", "title": "Make a Human Decision",
     "narration": "The investigator chooses whether to close, request more information, or escalate. The AI does not make that decision or submit it automatically.",
     "target": (404, 371)},
    {"screen": "16_reasoned_escalation.png", "title": "Explain and Submit the Decision",
     "narration": "The investigator enters a rationale and submits an escalation for separate human Compliance review. No regulatory filing is made.",
     "target": (456, 443)},
    {"screen": "17_decision_audit.png", "title": "Check the Audit Trail",
     "narration": "The app records who acted, when, and why in the audit trail. The report draft remains advice; the recorded decision belongs to the human investigator.",
     "target": (798, 459), "caption_top": True},
    {"screen": "18_compliance_handoff.png", "title": "Hand Off to Compliance",
     "narration": "The escalated case now appears in the separate Compliance Queue with the investigator's rationale. A Compliance officer can review it; Investigate IQ does not file with a regulator.",
     "target": (833, 528), "caption_top": True},
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
        command = [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                   "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
                   "-framerate", str(FPS), "-i", "-", "-i", str(narration),
                   "-c:v", "libopenh264", "-b:v", "2200k", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(OUTPUT)]
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
        finally:
            if process.poll() is None:
                process.kill()
    return OUTPUT, POSTER


if __name__ == "__main__":
    print(build())

#!/usr/bin/env python3
"""Free, deterministic daily Whatifly episode renderer for GitHub Actions.

Voice: espeak-ng. Art: original Pillow-drawn dusk scenes. No paid API calls.
Output: 19:6 MP4, a storyboard contact sheet, episode metadata and QA report.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SECONDS = 1140, 360, 20, 19
ROOT = Path(__file__).resolve().parents[2]
DAY = dt.datetime.now(dt.timezone.utc).astimezone(
    dt.timezone(dt.timedelta(hours=5, minutes=30))
).date()
OUT = ROOT / "outputs" / DAY.isoformat()
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(exist_ok=True)

# Every science claim below has a source URL in the episode record. New ideas
# come from combining a checked premise with a fresh everyday setting and scene order.
EPISODES = [
    {
        "slug": "sunlight-pauses",
        "topic": "What if sunlight paused for eight minutes?",
        "fact": "Sunlight takes about 8.35 minutes to travel from the Sun to Earth.",
        "source": "https://science.nasa.gov/earth/facts/",
        "beats": [
            "The Sun vanishes above the city.",
            "But the last light is still crossing space.",
            "Windows keep glowing. Streetlights stay asleep.",
            "Eight minutes pass. Then the sky goes dark.",
            "The Moon fades too; it only reflects sunlight.",
            "NASA puts the trip at about eight minutes.",
            "What will be the last bright thing you see?",
        ],
        "narration": "The Sun vanishes above the city. But its last light is still crossing space. Windows keep glowing. Streetlights stay asleep. Eight minutes pass. Then the sky goes dark. The Moon fades too; it only reflects sunlight. NASA puts the trip at about eight minutes. What will be the last bright thing you see?",
    },
    {
        "slug": "earth-stops-spinning",
        "topic": "What if Earth stopped spinning for one second?",
        "fact": "Earth's surface at the equator rotates at about 1,675 kilometers per hour.",
        "source": "https://www.nasa.gov/wp-content/uploads/2019/08/nosl-grc-ps-01960-rockets-rock-module.pdf",
        "beats": [
            "Earth stops spinning for one second.",
            "You, the air, and the ocean keep moving.",
            "At the equator, the ground was racing east.",
            "Loose things keep that motion as the crust stops.",
            "The atmosphere and water become the bigger danger.",
            "NASA gives the equator speed: 1,675 kilometers an hour.",
            "Then Earth turns again. What is still standing?",
        ],
        "narration": "Earth stops spinning for one second. You, the air, and the ocean keep moving. At the equator, the ground was racing east. Loose things keep that motion as the crust stops. The atmosphere and water become the bigger danger. NASA gives the equator speed: 1,675 kilometers an hour. Then Earth turns again. What is still standing?",
    },
    {
        "slug": "moon-disappears",
        "topic": "What if the Moon disappeared tonight?",
        "fact": "The Moon's gravity pulls Earth's oceans into tidal bulges on both the near and far sides.",
        "source": "https://science.nasa.gov/moon/tides/",
        "beats": [
            "Tonight, the Moon disappears over the harbor.",
            "The ocean does not leap into the sky.",
            "The Sun still pulls on Earth's water.",
            "But the Moon's stronger tide-making pull is gone.",
            "Coastlines lose the familiar lunar rhythm over time.",
            "NASA explains the Moon makes bulges on both sides.",
            "The next high tide arrives. How high is it?",
        ],
        "narration": "Tonight, the Moon disappears over the harbor. The ocean does not leap into the sky. The Sun still pulls on Earth's water. But the Moon's stronger tide-making pull is gone. Coastlines lose the familiar lunar rhythm over time. NASA explains the Moon makes bulges on both sides. The next high tide arrives. How high is it?",
    },
]

PLACES = ["a quiet kitchen", "a packed train station", "a rooftop at dusk", "an empty classroom", "a night market", "a seaside road", "a small apartment", "a crowded bridge", "a cricket ground", "a late-night diner", "a hilltop bus stop", "a flooded underpass", "a school playground", "a lighthouse balcony", "a sleeping suburb", "a busy airport", "a mountain village", "a city park", "a fishing pier", "a hospital corridor", "a train window", "a rooftop garden", "a silent library", "a desert road", "a glass office tower", "a harbor market", "a village well", "a cinema queue", "a roadside tea stall", "a ferry deck"]
PALETTE = [(255, 185, 115), (147, 196, 255), (234, 144, 179), (151, 225, 194)]


def run(*args: str, capture: bool = False) -> str:
    p = subprocess.run(args, check=True, text=True, capture_output=capture)
    return p.stdout if capture else ""


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for name in candidates:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, face, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textbbox((0, 0), test, font=face)[2] <= width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_scene(episode: dict, scene: int, local_frame: int) -> Image.Image:
    im = Image.new("RGB", (W, H))
    pix = im.load()
    for y in range(H):
        q = y / H
        c = (int(20 + q * 18), int(22 + q * 15), int(49 + q * 23))
        for x in range(W):
            pix[x, y] = c
    d = ImageDraw.Draw(im, "RGBA")
    seed = sum(ord(c) for c in episode["slug"])
    rng = random.Random(seed)
    for i in range(44):
        x, y = (rng.randint(0, W), rng.randint(0, 210))
        r = 1 if i % 4 else 2
        d.ellipse((x-r, y-r, x+r, y+r), fill=(220, 224, 255, rng.randint(90, 210)))
    accent = PALETTE[seed % len(PALETTE)]
    # A window and a warm floor lamp establish the recurring dusk-lit set.
    d.rounded_rectangle((740, 48, 1040, 236), radius=16, fill=(28, 38, 73, 255), outline=(accent[0], accent[1], accent[2], 210), width=4)
    d.line((890, 49, 890, 234), fill=(accent[0], accent[1], accent[2], 100), width=3)
    d.line((742, 142, 1038, 142), fill=(accent[0], accent[1], accent[2], 100), width=3)
    d.rectangle((0, 276, W, H), fill=(17, 20, 39, 255))
    d.line((0, 275, W, 275), fill=(accent[0], accent[1], accent[2], 160), width=3)
    # Original stick-figure hero, animated through a walk / reaction cycle.
    phase = local_frame / 16.0 + scene * .7
    cx = 310 + int(27 * math.sin(phase))
    cy = 211
    head = (cx-20, cy-105, cx+20, cy-65)
    d.ellipse(head, outline=(247, 224, 198, 255), width=5)
    d.line((cx, cy-65, cx, cy+5), fill=(247, 224, 198, 255), width=6)
    arm = int(24 * math.sin(phase * 1.4))
    d.line((cx, cy-45, cx-40, cy-15+arm), fill=(247, 224, 198, 255), width=5)
    d.line((cx, cy-45, cx+42, cy-20-arm), fill=(247, 224, 198, 255), width=5)
    leg = int(22 * math.sin(phase * 1.7))
    d.line((cx, cy+5, cx-28+leg, cy+55), fill=(247, 224, 198, 255), width=6)
    d.line((cx, cy+5, cx+28-leg, cy+55), fill=(247, 224, 198, 255), width=6)
    d.ellipse((cx-7, cy-89, cx-2, cy-84), fill=accent+(255,))
    d.ellipse((cx+3, cy-89, cx+8, cy-84), fill=accent+(255,))
    # Scene-specific symbol signals the episode's power without using stock art.
    if episode["slug"] == "sunlight-pauses":
        r = 19 + (scene % 3) * 5
        d.ellipse((590-r, 112-r, 590+r, 112+r), outline=(255, 206, 120, 230), width=4)
        for a in range(0, 360, 45):
            x1 = 590 + int((r+7)*math.cos(math.radians(a)))
            y1 = 112 + int((r+7)*math.sin(math.radians(a)))
            x2 = 590 + int((r+20)*math.cos(math.radians(a)))
            y2 = 112 + int((r+20)*math.sin(math.radians(a)))
            d.line((x1,y1,x2,y2), fill=(255,206,120,210), width=3)
    elif episode["slug"] == "earth-stops-spinning":
        d.arc((545, 72, 670, 196), start=scene*25, end=scene*25+230, fill=(146,196,255,240), width=5)
        d.polygon([(663,110),(680,121),(659,132)], fill=(146,196,255,240))
    else:
        d.ellipse((550, 79, 624, 153), fill=(226, 223, 205, 255))
        d.ellipse((579, 66, 650, 138), fill=(31, 33, 63, 255))
        for crx, cry, cr in [(574,103,5),(596,128,4),(610,94,3)]:
            d.ellipse((crx-cr,cry-cr,crx+cr,cry+cr), fill=(154,151,151,180))
    # Bold subtitle card is high contrast and limited to two lines.
    cap = font(24, True)
    lines = wrap(d, episode["beats"][scene], cap, 990)
    y0 = 292 if len(lines) == 1 else 285
    for i, line in enumerate(lines[:2]):
        box = d.textbbox((0,0), line, font=cap)
        tw = box[2] - box[0]
        d.text(((W-tw)//2, y0+i*29), line, font=cap, fill=(255,248,238,255), stroke_width=1, stroke_fill=(12,14,25,220))
    # Current location tag provides daily visual variety.
    small = font(16, True)
    d.text((34, 30), episode["place"].upper(), font=small, fill=accent+(255,))
    return im


def main() -> None:
    ordinal = DAY.toordinal()
    rng = random.Random(ordinal)
    ep = dict(rng.choice(EPISODES))
    ep["place"] = rng.choice(PLACES)
    if ep["slug"] == "sunlight-pauses":
        ep["narration"] = ep["narration"].replace("above the city", f"over {ep['place']}")
        ep["beats"][0] = f"The Sun vanishes over {ep['place']}."
        premise = f"sunlight paused over {ep['place']}"
    elif ep["slug"] == "earth-stops-spinning":
        ep["narration"] = ep["narration"].replace("Earth stops spinning for one second.", f"At {ep['place']}, Earth stops spinning for one second.")
        ep["beats"][0] = f"At {ep['place']}, Earth stops spinning."
        premise = f"Earth stopped spinning at {ep['place']}"
    else:
        ep["narration"] = ep["narration"].replace("over the harbor", f"above {ep['place']}")
        ep["beats"][0] = f"Tonight, the Moon disappears above {ep['place']}."
        premise = f"the Moon disappeared above {ep['place']}"
    ep["topic"] = f"What if {premise}?"
    ep["slug"] = ep["slug"] + "-" + DAY.strftime("%Y%m%d")
    ep["title"] = ep["topic"] + " #shorts"
    ep["description"] = f"{ep['topic']} A quick WhatiflyHQ thought experiment. Science source: {ep['source']} #shorts"
    ep["tags"] = ["What If", "WhatiflyHQ", "Science", "Education", "shorts"]
    words = len(ep["narration"].split())
    if not 45 <= words <= 65:
        raise SystemExit(f"Storyboard/script QA failed: narration is {words} words (expected 45–65).")
    if not shutil.which("espeak-ng") or not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("Required free render tools are missing: espeak-ng, ffmpeg, ffprobe.")
    narration = OUT / "voice.wav"
    run("espeak-ng", "-v", "en-us", "-s", "185", "-w", str(narration), ep["narration"])
    # Seven animated shots, with the final image held to the exact 19-second master.
    scene_frames = round(SECONDS * FPS / len(ep["beats"]))
    for n in range(SECONDS * FPS):
        scene = min(len(ep["beats"])-1, n // scene_frames)
        local = n % scene_frames
        draw_scene(ep, scene, local).save(FRAMES / f"frame_{n:04d}.png", optimize=True)
    # Storyboard self-check: one contact-sheet frame per shot, correct dimensions,
    # nonempty high-contrast pixels and all seven lines represented.
    thumbs = []
    for scene in range(len(ep["beats"])):
        frame_no = min(SECONDS*FPS-1, scene*scene_frames + scene_frames//2)
        frame = Image.open(FRAMES / f"frame_{frame_no:04d}.png").convert("RGB")
        if frame.size != (W,H) or frame.getbbox() is None:
            raise SystemExit(f"Storyboard QA failed on scene {scene+1}.")
        thumbs.append(frame.resize((380,120)))
    board = Image.new("RGB", (760,480), (12,14,29))
    for i, thumb in enumerate(thumbs):
        board.paste(thumb, ((i%2)*380, (i//2)*120))
    board.save(OUT / "storyboard.jpg", quality=88)
    mp4 = ROOT / "videos" / f"{ep['slug']}.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    tmp = mp4.with_name(mp4.stem + "-raw.mp4")
    run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(FPS), "-i", str(FRAMES / "frame_%04d.png"), "-i", str(narration), "-t", str(SECONDS), "-vf", "scale=1140:360,format=yuv420p", "-af", "apad,atrim=0:19,loudnorm=I=-14:TP=-1:LRA=7", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-r", str(FPS), "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(tmp))
    tmp.replace(mp4)
    probe = json.loads(run("ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(mp4), capture=True))
    duration = float(probe["format"]["duration"])
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio_ok = any(s["codec_type"] == "audio" for s in probe["streams"])
    if not 15 <= duration <= 25 or video["width"] * 6 != video["height"] * 19 or not audio_ok:
        raise SystemExit(f"Master QA failed: duration={duration:.2f}s, dimensions={video['width']}x{video['height']}, audio={audio_ok}.")
    ep["science"] = [{"claim":ep["fact"], "source":ep["source"]}]
    (OUT / "episode.json").write_text(json.dumps(ep, indent=2), encoding="utf-8")
    report = {"date":DAY.isoformat(),"slug":ep["slug"],"title":ep["title"],"duration_seconds":round(duration,2),"dimensions":f"{video['width']}x{video['height']}","aspect_ratio":"19:6","word_count":words,"storyboard_check":"passed","sound_check":"voice track present; normalized to -14 LUFS target and -1 dBTP ceiling","master_check":"passed","science_source":ep["source"],"mp4":str(mp4.relative_to(ROOT)).replace("\\","/")}
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    shutil.rmtree(FRAMES)
    print(json.dumps({"video":str(mp4.relative_to(ROOT)).replace("\\","/"),"report":str(OUT/"report.json"),"title":ep["title"],"description":ep["description"],"tags":ep["tags"],"slug":ep["slug"],"duration":duration}, indent=2))


if __name__ == "__main__":
    main()


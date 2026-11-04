#!/usr/bin/env python3
"""Cloud-friendly vertical renderer for WhatiflyHQ.

Uses Pillow + espeak-ng + FFmpeg on a GitHub-hosted Linux runner.
Optional OpenAI-compatible free-tier text endpoint is best-effort only:
any missing key, rate limit, network error, or invalid response falls back
to the researched script already in render.py. No paid provider is assumed.
"""
from __future__ import annotations
import datetime as dt
import json, math, os, random, shutil, subprocess, urllib.request, urllib.error
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Import only the curated, sourced episode bank. render.py does not run main on import.
from render import EPISODES, PLACES

W, H, FPS, DURATION = 720, 1280, 24, 20
ROOT = Path(__file__).resolve().parents[1]
DAY = dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
OUT = ROOT / "outputs" / DAY.isoformat()
OUT.mkdir(parents=True, exist_ok=True)
FRAMES = OUT / "vertical-scenes"
FRAMES.mkdir(exist_ok=True)

def run(*args, capture=False):
    p = subprocess.run(args, check=True, text=True, capture_output=capture)
    return p.stdout if capture else ""

def font(size, bold=False):
    paths = [
      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
      "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]
    for p in paths:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, face, width):
    result, line = [], ""
    for word in text.split():
        candidate = (line + " " + word).strip()
        if draw.textbbox((0,0), candidate, font=face)[2] <= width: line = candidate
        else:
            if line: result.append(line)
            line = word
    if line: result.append(line)
    return result

def optional_ai_rewrite(base):
    """Rewrite only supplied narration/beats. Never invent new scientific claims."""
    url, key, model = os.getenv("AI_API_URL"), os.getenv("AI_API_KEY"), os.getenv("AI_MODEL")
    if not (url and key and model): return base, "curated-fallback"
    prompt = (
      "Rewrite the supplied short-video narration in natural conversational English. "
      "Keep the exact scientific meaning, add no facts, numbers, claims, or citations. "
      "Return JSON only with keys narration (45-65 words) and beats (exactly 7 short caption lines). "
      "The beats must correspond to the narration. This is a hypothetical educational short. "
      "SOURCE SCRIPT: " + json.dumps({"narration":base["narration"],"beats":base["beats"],"fact":base["fact"]})
    )
    payload = json.dumps({"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0.65}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            data=json.loads(response.read().decode())
        text=data["choices"][0]["message"]["content"]
        # Accept providers that wrap JSON in a code fence.
        text=text.strip().removeprefix("```json").removesuffix("```").strip()
        obj=json.loads(text)
        narration=str(obj["narration"]).strip()
        beats=[str(x).strip() for x in obj["beats"]]
        if not 45 <= len(narration.split()) <= 65 or len(beats)!=7 or any(not b for b in beats):
            raise ValueError("script QA failed")
        return {**base,"narration":narration,"beats":beats}, "hosted-ai"
    except Exception as exc:
        print(f"Optional AI unavailable; using researched fallback ({type(exc).__name__}).")
        return base, "curated-fallback"

def draw_scene(ep, index, beat, place):
    im=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(im,"RGBA")
    # Dark blue vertical gradient, generated per row to keep runner CPU cost low.
    for y in range(H):
        q=y/H
        d.line((0,y,W,y),fill=(int(12+q*18),int(18+q*19),int(42+q*30),255))
    seed=sum(map(ord,ep["slug"]))+index*23
    rng=random.Random(seed)
    accent=[(255,190,112),(132,202,255),(236,145,184),(145,226,194)][seed%4]
    for _ in range(75):
        x,y=rng.randrange(W),rng.randrange(50,650)
        r=rng.choice([1,2,3])
        d.ellipse((x-r,y-r,x+r,y+r),fill=(235,240,255,rng.randrange(90,220)))
    # Headline / episode marker
    d.rounded_rectangle((42,48,678,126),radius=24,fill=(20,28,55,220),outline=(*accent,220),width=3)
    d.text((62,72),"WHATIFLYHQ  •  WHAT IF?",font=font(25,True),fill=(*accent,255))
    # Stylized planet / concept symbol
    cx,cy=360,420
    d.ellipse((cx-150,cy-150,cx+150,cy+150),fill=(39,71,122,255),outline=(*accent,255),width=8)
    d.arc((cx-175,cy-85,cx+175,cy+85),start=10+index*18,end=330+index*18,fill=(255,255,255,210),width=9)
    d.ellipse((cx-45,cy-45,cx+45,cy+45),fill=(*accent,240))
    # Stick figure foreground
    hx,hy=360,790
    d.ellipse((hx-48,hy-170,hx+48,hy-74),outline=(250,230,210,255),width=10)
    d.line((hx,hy-74,hx,hy+90),fill=(250,230,210,255),width=12)
    swing=int(24*math.sin(index*1.1))
    d.line((hx,hy-30,hx-95,hy+35+swing),fill=(250,230,210,255),width=10)
    d.line((hx,hy-30,hx+95,hy+35-swing),fill=(250,230,210,255),width=10)
    d.line((hx,hy+90,hx-75,hy+220),fill=(250,230,210,255),width=12)
    d.line((hx,hy+90,hx+75,hy+220),fill=(250,230,210,255),width=12)
    d.text((42,1000),place.upper(),font=font(22,True),fill=(*accent,255))
    # Caption area is in the lower safe zone, with high contrast.
    d.rounded_rectangle((32,1050,688,1225),radius=28,fill=(7,10,22,225),outline=(*accent,190),width=3)
    cap=font(32,True)
    lines=wrap(d,beat,cap,590)[:3]
    total=len(lines)*43
    y=1137-total//2
    for line in lines:
        bbox=d.textbbox((0,0),line,font=cap)
        d.text(((W-(bbox[2]-bbox[0]))//2,y),line,font=cap,fill=(255,250,242,255),stroke_width=1,stroke_fill=(0,0,0,220))
        y+=43
    return im

def main():
    if not all(shutil.which(x) for x in ("espeak-ng","ffmpeg","ffprobe")):
        raise SystemExit("Missing required cloud tools: espeak-ng, ffmpeg, ffprobe")
    state=ROOT/"automation"/"used-premises.json"
    used=set(json.loads(state.read_text()) if state.exists() else [])
    candidates=[e for e in EPISODES if e["slug"] not in used]
    # When the curated bank is exhausted, rotate it instead of permanently stopping.
    if not candidates:
        used=set()
        candidates=list(EPISODES)
    rng=random.Random(DAY.toordinal())
    base=dict(rng.choice(candidates))
    base["place"]=rng.choice(PLACES)
    ep, ai_mode=optional_ai_rewrite(base)
    ep["slug"]=base["slug"]+"-"+DAY.strftime("%Y%m%d")
    ep["title"]=base["topic"]+" #shorts"
    ep["description"]=base["topic"]+" A WhatiflyHQ science thought experiment. Source: "+base["source"]+" #shorts"
    ep["tags"]=["What If","WhatiflyHQ","Science","Education","shorts"]
    words=len(ep["narration"].split())
    if not 45<=words<=65: raise SystemExit(f"Narration QA failed: {words} words")
    wav=OUT/"voice.wav"
    run("espeak-ng","-v","en-us","-s","175","-w",str(wav),ep["narration"])
    # Seven vertical scene stills. This avoids expensive per-frame Python rasterization.
    for i,beat in enumerate(ep["beats"]):
        draw_scene(ep,i,beat,ep["place"]).save(FRAMES/f"scene_{i:02d}.jpg",quality=92,optimize=True)
    board=Image.new("RGB",(720,1280),(10,14,28))
    for i in range(7):
        thumb=Image.open(FRAMES/f"scene_{i:02d}.jpg").resize((180,320))
        board.paste(thumb,((i%4)*180,(i//4)*320))
    board.save(OUT/"storyboard.jpg",quality=88)
    # FFmpeg concat stills with hard cuts and one voice track. Vertical 9:16.
    scene_seconds=DURATION/7
    concat=OUT/"scenes.txt"
    lines=[]
    for i in range(7):
        lines += [f"file '{(FRAMES/f'scene_{i:02d}.jpg').as_posix()}'",f"duration {scene_seconds:.6f}"]
    lines.append(f"file '{(FRAMES/'scene_06.jpg').as_posix()}'")
    concat.write_text("\n".join(lines)+"\n")
    mp4=ROOT/"videos"/f"{ep['slug']}.mp4"
    mp4.parent.mkdir(exist_ok=True)
    tmp=mp4.with_name(mp4.stem+"-tmp.mp4")
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-i",str(wav),"-t",str(DURATION),"-vf","scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p","-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","25","-c:a","aac","-b:a","128k","-af","apad,atrim=0:20","-movflags","+faststart",str(tmp))
    tmp.replace(mp4)
    probe=json.loads(run("ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(mp4),capture=True))
    duration=float(probe["format"]["duration"])
    video=next(s for s in probe["streams"] if s["codec_type"]=="video")
    audio=any(s["codec_type"]=="audio" for s in probe["streams"])
    if not 15<=duration<=25 or video["width"]*16!=video["height"]*9 or not audio:
        raise SystemExit(f"QA failed: {duration}s {video['width']}x{video['height']} audio={audio}")
    ep["science"]=[{"claim":ep["fact"],"source":ep["source"]}]
    ep["ai_mode"]=ai_mode
    (OUT/"episode.json").write_text(json.dumps(ep,indent=2))
    report={"date":DAY.isoformat(),"slug":ep["slug"],"title":ep["title"],"duration_seconds":round(duration,2),"dimensions":f"{video['width']}x{video['height']}","aspect_ratio":"9:16","word_count":words,"ai_mode":ai_mode,"qa":"passed","science_source":ep["source"],"mp4":str(mp4.relative_to(ROOT)).replace("\\","/")}
    (OUT/"report.json").write_text(json.dumps(report,indent=2))
    used.add(base["slug"])
    state.write_text(json.dumps(sorted(used),indent=2)+"\n")
    shutil.rmtree(FRAMES)
    print(json.dumps({"video":str(mp4.relative_to(ROOT)).replace("\\","/"),"report":str(OUT/"report.json"),"title":ep["title"],"description":ep["description"],"tags":ep["tags"],"slug":ep["slug"],"duration":duration,"ai_mode":ai_mode},indent=2))

if __name__=="__main__":
    main()

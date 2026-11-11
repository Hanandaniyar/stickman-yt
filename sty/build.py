"""Menyusun komposisi HyperFrames (build/index.html) dari adegan, timing, narasi, musik, dan subtitle."""
import html
import json
import shutil
from pathlib import Path

from sty.config import PROJECT_ROOT, load_config
from sty.episode import validate_narration

TAIL_S = 1.0
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
STICKMAN_LIB = PROJECT_ROOT / "lib" / "stickman"


def _num(x: float) -> str:
    return f"{round(x, 3):g}" if x != int(x) else f"{x:.1f}"


def caption_groups(words: list[dict], max_words: int = 5, pause: float = 0.15) -> list[list[dict]]:
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        sentence_end = w["w"].rstrip("\"')").endswith((".", "?", "!"))
        gap = nxt is not None and nxt["start"] - w["end"] >= pause
        if len(cur) >= max_words or sentence_end or gap or nxt is None:
            groups.append(cur)
            cur = []
    return groups


def _captions_html(words: list[dict], total: float) -> str:
    rows, tweens = [], []
    for g, group in enumerate(caption_groups(words)):
        start = max(0.1, group[0]["start"] - 0.05)
        end = min(total, group[-1]["end"] + 0.15)
        spans = " ".join(f'<span id="cap-{g}-{i}">{html.escape(w["w"])}</span>' for i, w in enumerate(group))
        rows.append(
            f'    <div id="cap-{g}" class="clip cap" data-start="{_num(start)}" data-duration="{_num(end - start)}">{spans}</div>'
        )
        for i, w in enumerate(group):
            tweens.append(f'    tl.set("#cap-{g}-{i}", {{ color: "#1F9D55" }}, {_num(w["start"])});')
            tweens.append(f'    tl.set("#cap-{g}-{i}", {{ color: "#111111" }}, {_num(max(w["end"], w["start"] + 0.05))});')
    return f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; }}
    .cap {{ position: absolute; left: 0; width: 1920px; bottom: 100px; text-align: center; overflow: visible;
      font-family: "Montserrat"; font-weight: 800; font-size: 64px; line-height: 1.15; color: #111111; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
{chr(10).join(rows)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tweens)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""


def build_composition(ep: Path) -> Path:
    ep = Path(ep)
    timing_path = ep / "timing.json"
    if not timing_path.exists() or not (ep / "audio" / "narration.wav").exists():
        raise FileNotFoundError("timing.json/narration.wav belum ada: jalankan sty voice dulu")
    errs = validate_narration(ep)
    if errs:
        raise ValueError("storyboard belum valid:\n" + "\n".join(errs))
    timing = json.loads(timing_path.read_text())
    narration = json.loads((ep / "narration.json").read_text())
    if [s["id"] for s in timing["scenes"]] != [s["id"] for s in narration["scenes"]]:
        raise ValueError("daftar adegan di timing.json tidak cocok dengan narration.json: jalankan sty voice --force")
    cfg = load_config()
    total = round(timing["duration"] + TAIL_S, 3)

    build = ep / "build"
    if build.exists():
        shutil.rmtree(build)
    (build / "compositions").mkdir(parents=True)
    (build / "assets").mkdir()
    shutil.copytree(STICKMAN_LIB, build / "assets" / "stickman", ignore=shutil.ignore_patterns("demo", "README.md"))
    shutil.copy(ep / "audio" / "narration.wav", build / "assets" / "narration.wav")

    hosts = []
    scenes = timing["scenes"]
    for i, sc in enumerate(scenes):
        sid = sc["id"]
        shutil.copy(ep / "scenes" / f"{sid}.html", build / "compositions" / f"{sid}.html")
        end = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
        hosts.append(
            f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html"'
            f' data-start="{_num(sc["start"])}" data-duration="{_num(end - sc["start"])}" data-track-index="1"'
            f' data-track-kind="graphics" data-width="1920" data-height="1080"></div>'
        )
    (build / "compositions" / "captions.html").write_text(_captions_html(timing["words"], total))
    hosts.append(
        f'      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html"'
        f' data-start="0" data-duration="{_num(total)}" data-track-index="2" data-track-kind="captions"'
        f' data-width="1920" data-height="1080" style="z-index: 10"></div>'
    )
    audio = [
        '      <audio id="narration" class="clip" src="assets/narration.wav" data-start="0"'
        ' data-track-index="3" data-volume="1"></audio>'
    ]
    music = narration.get("music")
    if music:
        src = PROJECT_ROOT / music if not (ep.parent.parent / music).exists() else ep.parent.parent / music
        dest = build / "assets" / f"music{src.suffix}"
        shutil.copy(src, dest)
        audio.append(
            f'      <audio id="music" class="clip" src="assets/{dest.name}" data-start="0" data-duration="{_num(total)}"'
            f' data-track-index="4" data-volume="{cfg["music_volume"]}" data-fade-in="1" data-fade-out="2"></audio>'
        )

    index = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="{GSAP}"></script>
    <link rel="stylesheet" href="assets/stickman/stickman.css" />
    <script src="assets/stickman/stickman.js"></script>
    <style>
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #FAF7F0; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{_num(total)}"
         data-width="1920" data-height="1080">
{chr(10).join(hosts + audio)}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
    out = build / "index.html"
    out.write_text(index)
    return out


def register(sub) -> None:
    from sty.episode import episode_dir

    p = sub.add_parser("build", help="susun komposisi HyperFrames di episodes/<ep>/build")
    p.add_argument("ep")
    p.add_argument("--root", default=str(PROJECT_ROOT))
    p.set_defaults(func=lambda a: print(build_composition(episode_dir(a.ep, a.root))))

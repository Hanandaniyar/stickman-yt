"""Menyusun komposisi HyperFrames (build/index.html) dari adegan, timing, narasi, musik, dan subtitle."""
import html
import json
import shutil
from pathlib import Path

from sty.config import PROJECT_ROOT, load_config
from sty.episode import BG_LIB, FORMATS, EMOJI_LIB, EMOJI_RE, _words, sfx_path, background_names, validate_narration

TAIL_S = 1.0
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
STICKMAN_LIB = PROJECT_ROOT / "lib" / "stickman"


def _num(x: float) -> str:
    return f"{round(x, 3):g}" if x != int(x) else f"{x:.1f}"


def _media_duration(path: Path) -> float:
    import soundfile as sf

    return float(sf.info(str(path)).duration)


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


def _captions_html(words: list[dict], total: float, fw: int = 1920, fh: int = 1080) -> str:
    short = fh > fw
    rows, tweens = [], []
    groups = caption_groups(words, max_words=3 if short else 5)
    starts = [max(0.1, grp[0]["start"] - 0.05) for grp in groups]
    for g, group in enumerate(groups):
        start = starts[g]
        end = min(total, group[-1]["end"] + 0.15)
        if g + 1 < len(groups):
            end = min(end, starts[g + 1])  # satu baris subtitle saja di layar
        spans = " ".join(f'<span id="cap-{g}-{i}">{html.escape(w["w"])}</span>' for i, w in enumerate(group))
        rows.append(
            f'    <div id="cap-{g}" class="clip cap" data-start="{_num(start)}" data-duration="{_num(end - start)}">{spans}</div>'
        )
        for i, w in enumerate(group):
            tweens.append(f'    tl.set("#cap-{g}-{i}", {{ color: "#1F9D55" }}, {_num(w["start"])});')
            tweens.append(f'    tl.set("#cap-{g}-{i}", {{ color: "#111111" }}, {_num(max(w["end"], w["start"] + 0.05))});')
    pos = "top: 300px;" if short else "bottom: 100px;"
    fs = 96 if short else 64
    extra = " -webkit-text-stroke: 16px #FAF7F0; paint-order: stroke fill;" if short else ""
    return f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; }}
    .cap {{ position: absolute; left: 0; width: {fw}px; {pos} text-align: center; overflow: visible;
      font-family: "Montserrat"; font-weight: 800; font-size: {fs}px; line-height: 1.15; color: #111111;{extra} }}
  </style>
  <div id="root" data-composition-id="captions" data-width="{fw}" data-height="{fh}">
{chr(10).join(rows)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tweens)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""


SFX_VOLUME = 0.35


def _sfx_clips(build: Path, scenes: list[dict], timing: dict, total: float) -> list[str]:
    """Efek suara per adegan: 'at' = detik sejak adegan mulai, atau 'word' = saat kata itu diucapkan."""
    clips, lengths = [], {}
    slots = {s["id"]: s for s in timing["scenes"]}
    for sc in scenes:
        slot = slots[sc["id"]]
        for cue in sc.get("sfx") or []:
            name = cue["name"]
            if "word" in cue:
                hits = [w for w in timing["words"] if slot["start"] - 0.05 <= w["start"] <= slot["end"] + 0.05
                        and cue["word"].lower() in _words(w["w"])]
                if not hits:
                    print(f"peringatan: {sc['id']}: kata '{cue['word']}' tidak ditemukan di timing, efek '{name}' dilewati")
                    continue
                start = hits[0]["start"] + float(cue.get("offset", 0))
            else:
                start = slot["start"] + float(cue["at"])
            if start >= total - 0.05:
                continue
            dest = build / "assets" / "sfx" / f"{name}.mp3"
            if name not in lengths:
                dest.parent.mkdir(exist_ok=True)
                shutil.copy(sfx_path(name), dest)
                lengths[name] = _media_duration(dest)
            dur = min(lengths[name], total - start)
            vol = cue.get("volume", SFX_VOLUME)
            clips.append(
                f'      <audio id="sfx-{len(clips)}" class="clip" src="assets/sfx/{name}.mp3" data-start="{_num(start)}"'
                f' data-duration="{_num(dur)}" data-track-index="5" data-volume="{vol}"></audio>'
            )
    return clips


def _bundle_backgrounds(ep: Path, build: Path, sids: list[str]) -> None:
    """Salin hanya latar yang dipakai, plus backgrounds.js yang mendaftarkannya (dimuat sinkron di <head>)."""
    used = set()
    for sid in sids:
        used |= background_names((ep / "scenes" / f"{sid}.html").read_text())
    dest = build / "assets" / "backgrounds"
    dest.mkdir()
    data = {}
    for name in sorted(used):
        shutil.copy(BG_LIB / f"{name}.svg", dest / f"{name}.svg")
        data[name] = (BG_LIB / f"{name}.svg").read_text()
    (dest / "backgrounds.js").write_text(
        "/* dibuat oleh sty build: latar yang dipakai episode ini */\n"
        f"Stickman.registerBackgrounds({json.dumps(data, ensure_ascii=False)});\n"
    )


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
    W, H = FORMATS[narration.get("format", "landscape")]
    total = round(timing["duration"] + TAIL_S, 3)

    build = ep / "build"
    if build.exists():
        shutil.rmtree(build)
    (build / "compositions").mkdir(parents=True)
    (build / "assets").mkdir()
    shutil.copytree(STICKMAN_LIB, build / "assets" / "stickman", ignore=shutil.ignore_patterns("demo", "README.md"))
    shutil.copy(ep / "audio" / "narration.wav", build / "assets" / "narration.wav")

    used = set()
    for sc in timing["scenes"]:
        used |= set(EMOJI_RE.findall((ep / "scenes" / f"{sc['id']}.html").read_text()))
    if used:
        (build / "assets" / "emoji").mkdir()
        for name in sorted(used):
            shutil.copy(EMOJI_LIB / f"{name}.svg", build / "assets" / "emoji" / f"{name}.svg")

    _bundle_backgrounds(ep, build, [sc["id"] for sc in timing["scenes"]])

    hosts = []
    scenes = timing["scenes"]
    for i, sc in enumerate(scenes):
        sid = sc["id"]
        shutil.copy(ep / "scenes" / f"{sid}.html", build / "compositions" / f"{sid}.html")
        end = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
        hosts.append(
            f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html"'
            f' data-start="{_num(sc["start"])}" data-duration="{_num(end - sc["start"])}" data-track-index="1"'
            f' data-track-kind="graphics" data-width="{W}" data-height="{H}"></div>'
        )
    (build / "compositions" / "captions.html").write_text(_captions_html(timing["words"], total, W, H))
    hosts.append(
        f'      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html"'
        f' data-start="0" data-duration="{_num(total)}" data-track-index="2" data-track-kind="captions"'
        f' data-width="{W}" data-height="{H}" style="z-index: 10"></div>'
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
        length = _media_duration(dest)
        if length <= 0.5:
            raise ValueError(f"musik '{music}' terlalu pendek atau tidak bisa dibaca")
        t, i = 0.0, 0
        while t < total - 1e-6:  # ulangi lagu sampai menutupi seluruh video
            dur = min(length, total - t)
            fades = ' data-fade-in="1"' if i == 0 else ""
            fades += ' data-fade-out="2"' if t + dur >= total - 1e-6 else ""
            audio.append(
                f'      <audio id="music-{i}" class="clip" src="assets/{dest.name}" data-start="{_num(t)}"'
                f' data-duration="{_num(dur)}" data-track-index="4" data-volume="{cfg["music_volume"]}"{fades}></audio>'
            )
            t, i = round(t + dur, 3), i + 1

    audio.extend(_sfx_clips(build, narration["scenes"], timing, total))

    index = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="{GSAP}"></script>
    <script>window.STICKMAN_FRAME = {{w: {W}, h: {H}}};</script>
    <link rel="stylesheet" href="assets/stickman/stickman.css" />
    <script src="assets/stickman/stickman.js"></script>
    <script src="assets/backgrounds/backgrounds.js"></script>
    <style>
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #FAF7F0; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{_num(total)}"
         data-width="{W}" data-height="{H}">
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

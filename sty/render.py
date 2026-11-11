"""Render video final, still untuk diperiksa Handur, preview untuk Telegram, dan thumbnail."""
import html
import json
import shutil
import subprocess
from pathlib import Path

from sty.build import STICKMAN_LIB, TAIL_S, build_composition
from sty.config import PROJECT_ROOT
from sty.notify import MAX_VIDEO_BYTES
from sty.voice import _run, hf

POSES = json.loads((STICKMAN_LIB / "poses.json").read_text())


def _total(ep: Path) -> float:
    return round(json.loads((ep / "timing.json").read_text())["duration"] + TAIL_S, 3)


def render_episode(ep: Path, run=subprocess.run) -> Path:
    ep = Path(ep)
    build = build_composition(ep)
    _run(run, hf("lint", str(build.parent)), "lint komposisi")
    out = ep / "final.mp4"
    _run(run, hf("render", str(build.parent), "-o", str(out), "--quality", "delivery", "--fps", "30", "--strict"), "render video")
    res = _run(run, ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(out)], "ffprobe")
    got, want = float(res.stdout.strip()), _total(ep)
    if abs(got - want) > 0.5:
        raise RuntimeError(f"durasi video {got:.2f} detik tidak sama dengan komposisi {want:.2f} detik")
    return out


def make_stills(ep: Path, run=subprocess.run) -> list[Path]:
    ep = Path(ep)
    build = ep / "build"
    if not (build / "index.html").exists():
        build_composition(ep)
    total = _total(ep)
    times = [1.0, total * 0.25, total * 0.5, total * 0.75, max(0.0, total - 1.0)]
    stills = ep / "stills"
    if stills.exists():
        shutil.rmtree(stills)
    _run(run, hf("snapshot", str(build), "--at", ",".join(f"{round(t, 2):g}" for t in times), "--no-end", "-o", str(stills)), "snapshot")
    return sorted(stills.glob("*.png"))


def make_preview(ep: Path, run=subprocess.run) -> Path | None:
    ep = Path(ep)
    out = ep / "preview.mp4"
    _run(run, ["ffmpeg", "-y", "-loglevel", "error", "-i", str(ep / "final.mp4"), "-vf", "scale=854:480",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "32", "-c:a", "aac", "-b:a", "64k", str(out)], "preview")
    if out.stat().st_size > MAX_VIDEO_BYTES:
        out.unlink()
        return None
    return out


def make_thumbnail(ep: Path, run=subprocess.run) -> Path:
    ep = Path(ep)
    lines = [l.strip() for l in (ep / "thumbnail.txt").read_text().splitlines() if l.strip()]
    text = lines[0] if lines else ""
    pose = "point"
    for l in lines[1:]:
        if l.lower().startswith("pose:"):
            pose = l.split(":", 1)[1].strip()
    if pose not in POSES:
        raise ValueError(f"pose thumbnail '{pose}' tidak dikenal; pilihan: {', '.join(POSES)}")
    thumb = ep / "build" / "thumb"
    if thumb.exists():
        shutil.rmtree(thumb)
    (thumb / "assets").mkdir(parents=True)
    shutil.copytree(STICKMAN_LIB, thumb / "assets" / "stickman", ignore=shutil.ignore_patterns("demo", "README.md"))
    page = (STICKMAN_LIB / "thumbnail.html").read_text()
    page = page.replace("{{TEXT}}", html.escape(text)).replace('pose: "{{POSE}}"', f'pose: "{pose}"')
    (thumb / "index.html").write_text(page)
    shots = thumb / "shots"
    _run(run, hf("snapshot", str(thumb), "--at", "0", "--no-end", "-o", str(shots)), "thumbnail")
    pngs = sorted(p for p in shots.glob("*.png") if p.name.startswith("frame"))
    if not pngs:
        raise RuntimeError("snapshot thumbnail tidak menghasilkan PNG")
    out = ep / "thumbnail.png"
    shutil.copy(pngs[0], out)
    return out


def register(sub) -> None:
    from sty.episode import episode_dir

    for name, fn, help_ in (
        ("render", render_episode, "render final.mp4"),
        ("stills", make_stills, "ambil 5 still untuk diperiksa"),
        ("preview", make_preview, "buat preview 480p untuk Telegram"),
        ("thumbnail", make_thumbnail, "render thumbnail.png dari thumbnail.txt"),
    ):
        p = sub.add_parser(name, help=help_)
        p.add_argument("ep")
        p.add_argument("--root", default=str(PROJECT_ROOT))
        p.set_defaults(func=lambda a, fn=fn: print(fn(episode_dir(a.ep, a.root))))

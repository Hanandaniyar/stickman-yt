"""Folder episode dan status.json."""
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sty.config import PROJECT_ROOT

STAGES = ["topics", "script", "scenes", "rendered", "metadata", "approved", "done"]
REQUESTS = ["render", "upload"]
APPROVALS = ["topic", "script", "final"]
VERDICTS = ["LOLOS", "REVISI"]


def episodes_root(root: Path) -> Path:
    return Path(root) / "episodes"


def _slugify(slug: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    if not s:
        raise ValueError("slug kosong")
    return s


def create_episode(slug: str, root: Path = PROJECT_ROOT) -> Path:
    base = episodes_root(root)
    base.mkdir(parents=True, exist_ok=True)
    nums = [int(p.name[:3]) for p in base.iterdir() if p.is_dir() and re.match(r"\d{3}-", p.name)]
    ep = base / f"{(max(nums) + 1 if nums else 1):03d}-{_slugify(slug)}"
    (ep / "reviews").mkdir(parents=True)
    (ep / "scenes").mkdir()
    save_status(ep, {
        "episode": ep.name, "stage": "topics", "request": None,
        "approvals": {k: False for k in APPROVALS}, "reviews": [],
        "release_url": None, "youtube_id": None, "last_error": None, "updated_at": None,
    })
    return ep


def episode_dir(ref: str, root: Path = PROJECT_ROOT) -> Path:
    base = episodes_root(root)
    ref = str(ref)
    if (base / ref).is_dir():
        return base / ref
    if ref.isdigit():
        prefix = f"{int(ref):03d}-"
        for p in sorted(base.glob(prefix + "*")):
            if p.is_dir():
                return p
    raise FileNotFoundError(f"episode '{ref}' tidak ditemukan")


def load_status(ep: Path) -> dict:
    return json.loads((Path(ep) / "status.json").read_text())


def save_status(ep: Path, status: dict) -> None:
    status["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fd, tmp = tempfile.mkstemp(dir=ep, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, Path(ep) / "status.json")


def _update(ep: Path, **changes) -> dict:
    st = load_status(ep)
    st.update(changes)
    save_status(ep, st)
    return st


def set_stage(ep: Path, stage: str) -> None:
    if stage not in STAGES:
        raise ValueError(f"stage '{stage}' tidak dikenal; pilihan: {', '.join(STAGES)}")
    _update(ep, stage=stage)


def revision_rounds(ep: Path, stage: str) -> int:
    return sum(1 for r in load_status(ep)["reviews"] if r["stage"] == stage and r["verdict"] == "REVISI")


def record_review(ep: Path, stage: str, verdict: str, notes_md: str) -> int:
    if verdict not in VERDICTS:
        raise ValueError(f"putusan harus LOLOS atau REVISI, bukan '{verdict}'")
    st = load_status(ep)
    rnd = sum(1 for r in st["reviews"] if r["stage"] == stage) + 1
    rel = f"reviews/{stage}-{rnd}.md"
    (Path(ep) / "reviews").mkdir(exist_ok=True)  # folder kosong tidak tersimpan di git
    (Path(ep) / rel).write_text(f"# {stage} — ronde {rnd}: {verdict}\n\n{notes_md.strip()}\n")
    st["reviews"].append({"stage": stage, "round": rnd, "verdict": verdict, "file": rel})
    save_status(ep, st)
    return rnd


def approve(ep: Path, which: str) -> None:
    if which not in APPROVALS:
        raise ValueError(f"persetujuan '{which}' tidak dikenal")
    st = load_status(ep)
    st["approvals"][which] = True
    if which == "final":
        st["stage"] = "approved"
    save_status(ep, st)


def _check_scene_file(html: str, sid: str) -> list[str]:
    """Kontrak sub-komposisi HyperFrames: isi di dalam <template>, id komposisi dan kunci timeline = sid."""
    errs = []
    if not re.search(r"<template\b", html):
        errs.append("isi adegan harus berada di dalam <template>")
    m = re.search(r'data-composition-id="([^"]+)"', html)
    if not m or m.group(1) != sid:
        errs.append(f'root harus punya data-composition-id="{sid}"')
    keys = re.findall(r"""__timelines\[\s*["']([^"']+)["']\s*\]""", html)
    if keys != [sid]:
        errs.append(f'harus mendaftarkan tepat satu window.__timelines["{sid}"]')
    return errs


SFX_LIB = PROJECT_ROOT / "lib" / "sfx"
EMOJI_LIB = PROJECT_ROOT / "lib" / "emoji"
EMOJI_RE = re.compile(r"assets/emoji/([A-Za-z0-9_-]+)\.svg")


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9']+", text.lower()) if w]


def _check_sfx(sc: dict) -> list[str]:
    errs = []
    for cue in sc.get("sfx") or []:
        name = str(cue.get("name", ""))
        if not (SFX_LIB / f"{name}.mp3").exists():
            errs.append(f"efek suara '{name}' tidak ada di lib/sfx")
        if "word" in cue:
            if str(cue["word"]).lower() not in _words(str(sc.get("text", ""))):
                errs.append(f"efek suara '{name}': kata '{cue['word']}' tidak ada di teks adegan")
        elif not isinstance(cue.get("at"), (int, float)) or cue["at"] < 0:
            errs.append(f"efek suara '{name}' butuh 'at' (detik >= 0) atau 'word'")
    return errs


def validate_narration(ep: Path) -> list[str]:
    ep = Path(ep)
    path = ep / "narration.json"
    if not path.exists():
        return ["narration.json tidak ada"]
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"narration.json bukan JSON valid: {e}"]
    scenes = data.get("scenes") or []
    if not scenes:
        return ["narration.json tidak punya adegan"]
    errs, seen = [], set()
    for idx, sc in enumerate(scenes, start=1):
        sid = str(sc.get("id", ""))
        if not re.fullmatch(r"s\d{2}", sid):
            errs.append(f"{sid or '?'}: id harus berformat sNN")
            continue
        if sid in seen:
            errs.append(f"{sid}: id duplikat")
        seen.add(sid)
        if int(sid[1:]) != idx:
            errs.append(f"{sid}: urutan salah, seharusnya s{idx:02d}")
        if not str(sc.get("text", "")).strip():
            errs.append(f"{sid}: teks narasi kosong")
        frag = ep / "scenes" / f"{sid}.html"
        if not frag.exists():
            errs.append(f"{sid}: scenes/{sid}.html tidak ada")
        else:
            errs.extend(f"{sid}: {e}" for e in _check_scene_file(frag.read_text(), sid))
            for name in sorted(set(EMOJI_RE.findall(frag.read_text()))):
                if not (EMOJI_LIB / f"{name}.svg").exists():
                    errs.append(f"{sid}: ilustrasi '{name}' tidak ada di lib/emoji (lihat INDEX.txt)")
        errs.extend(f"{sid}: {e}" for e in _check_sfx(sc))
    music = data.get("music")
    if music and not (ep.parent.parent / music).exists():
        errs.append(f"musik '{music}' tidak ditemukan")
    return errs


def request(ep: Path, what: str) -> None:
    if what not in REQUESTS:
        raise ValueError(f"permintaan '{what}' tidak dikenal")
    st = load_status(ep)
    if what == "render":
        errs = validate_narration(ep)
        if errs:
            raise ValueError("storyboard belum valid:\n" + "\n".join(errs))
        st["approvals"]["final"] = False  # video baru harus ditonton dan disetujui ulang
        save_status(ep, st)
    else:
        if st.get("youtube_id"):
            raise PermissionError(f"episode ini sudah diunggah (youtube_id {st['youtube_id']}); upload ganda ditolak")
        if not st["approvals"]["final"]:
            raise PermissionError("upload butuh persetujuan akhir pemilik (sty approve <ep> final)")
        if not st.get("release_url"):
            raise PermissionError("video belum di-render; jalankan sty request <ep> render dulu")
    _update(ep, request=what, last_error=None)


def _ep(args):
    return episode_dir(args.ep, args.root)


def register(sub) -> None:
    def add(name, func, help_, *, ep=True):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--root", default=str(PROJECT_ROOT), help=argparse_suppress())
        if ep:
            p.add_argument("ep")
        p.set_defaults(func=func)
        return p

    def new(a):
        print(create_episode(a.slug, a.root).name)

    p = add("new", new, "buat episode baru", ep=False)
    p.add_argument("slug")

    def status(a):
        if a.ep:
            print(json.dumps(load_status(episode_dir(a.ep, a.root)), indent=2, ensure_ascii=False))
            return
        base = episodes_root(a.root)
        for d in sorted(base.iterdir()) if base.exists() else []:
            if (d / "status.json").exists():
                st = load_status(d)
                print(f"{d.name:40} {st['stage']:10} request={st['request']} error={st['last_error']}")

    p = add("status", status, "tampilkan status episode", ep=False)
    p.add_argument("ep", nargs="?")

    def review(a):
        notes = Path(a.notes_file).read_text() if a.notes_file else ""
        print(f"ronde {record_review(_ep(a), a.stage, a.verdict, notes)}")

    p = add("review", review, "catat putusan Handur")
    p.add_argument("stage")
    p.add_argument("verdict", choices=VERDICTS)
    p.add_argument("--notes-file")

    def stage(a):
        set_stage(_ep(a), a.stage)

    p = add("stage", stage, "ubah stage")
    p.add_argument("stage", choices=STAGES)

    def approve_cmd(a):
        approve(_ep(a), a.which)

    p = add("approve", approve_cmd, "catat persetujuan pemilik")
    p.add_argument("which", choices=APPROVALS)

    def request_cmd(a):
        try:
            request(_ep(a), a.what)
        except (ValueError, PermissionError) as e:
            print(f"ditolak: {e}")
            return 1
        print(f"permintaan {a.what} dicatat; commit + push untuk menjalankannya di GitHub")

    p = add("request", request_cmd, "minta tahap render/upload di GitHub Actions")
    p.add_argument("what", choices=REQUESTS)

    def check(a):
        errs = validate_narration(_ep(a))
        print("\n".join(errs) if errs else "valid")
        return 1 if errs else 0

    add("check", check, "validasi narration.json dan fragmen adegan")


def argparse_suppress():
    import argparse

    return argparse.SUPPRESS

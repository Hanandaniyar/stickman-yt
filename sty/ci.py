"""Pembantu GitHub Actions: cari permintaan tertunda, jalankan, dan laporkan hasilnya."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from sty.config import PROJECT_ROOT
from sty.episode import _update, episode_dir, episodes_root, load_status, save_status, set_stage
from sty.notify import notify, notify_video


def pending_requests(root: Path = PROJECT_ROOT) -> list[tuple[Path, str]]:
    base = episodes_root(root)
    out = []
    for d in sorted(base.iterdir()) if base.exists() else []:
        if (d / "status.json").exists():
            req = load_status(d).get("request")
            if req:
                out.append((d, req))
    return out


def clear_request(ep: Path, error: str | None) -> None:
    _update(ep, request=None, last_error=error)


# --- langkah-langkah (dipisah agar bisa diganti di test) ---

def _sh(cmd: list[str], cwd: Path | None = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        tail = "\n".join((res.stderr or res.stdout).splitlines()[-20:])
        raise RuntimeError(f"{' '.join(cmd[:3])} gagal:\n{tail}")
    return res.stdout


def _branch(root: Path) -> str:
    name = os.environ.get("GITHUB_REF_NAME", "").strip()
    return name or _sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root).strip()


def _git_sync(root: Path) -> None:
    _sh(["git", "pull", "--rebase", "--autostash", "origin", _branch(root)], cwd=root)


_LOCAL_ONLY = shutil.ignore_patterns("audio", "build", "*.mp4")


def _git_publish(root: Path, msg: str, ep: Path | None = None, fields: list[str] | tuple = ()) -> None:
    """Commit + push folder episodes. Jika remote berubah (mis. Handur menulis review saat render),
    bangun ulang commit di atas versi remote: file CI disalin kembali, dan di status.json hanya
    `fields` milik CI yang ditimpa. Tidak pernah meninggalkan rebase setengah jadi."""
    branch = _branch(root)
    for _ in range(3):
        _sh(["git", "add", "-A", "episodes"], cwd=root)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root).returncode != 0:
            _sh(["git", "commit", "-m", msg], cwd=root)
        if subprocess.run(["git", "push", "origin", f"HEAD:{branch}"], cwd=root, capture_output=True).returncode == 0:
            return
        if ep is None:
            raise RuntimeError("git push ditolak dan tidak ada episode untuk digabung ulang")
        ours = load_status(ep)
        with tempfile.TemporaryDirectory() as tmp:
            backup = Path(tmp) / "ep"
            shutil.copytree(ep, backup, ignore=_LOCAL_ONLY)
            _sh(["git", "fetch", "origin", branch], cwd=root)
            _sh(["git", "reset", "--hard", f"origin/{branch}"], cwd=root)
            for f in backup.rglob("*"):
                if f.is_file() and f.name != "status.json":
                    dest = ep / f.relative_to(backup)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
        theirs = load_status(ep) if (ep / "status.json").exists() else ours
        for key in fields:
            theirs[key] = ours.get(key)
        save_status(ep, theirs)
    raise RuntimeError("git push gagal 3 kali")


def _tag(ep: Path) -> str:
    return f"ep-{ep.name[:3]}"


def _release_upload(ep: Path, files: list[Path]) -> str:
    tag = _tag(ep)
    if subprocess.run(["gh", "release", "view", tag], capture_output=True).returncode != 0:
        _sh(["gh", "release", "create", tag, "--title", ep.name, "--notes", f"Video episode {ep.name}"])
    _sh(["gh", "release", "upload", tag, *map(str, files), "--clobber"])
    return _sh(["gh", "release", "view", tag, "--json", "url", "-q", ".url"]).strip()


def _release_download(ep: Path) -> Path:
    _sh(["gh", "release", "download", _tag(ep), "-p", "final.mp4", "-D", str(ep), "--clobber"])
    return ep / "final.mp4"


def _step_voice(ep):
    from sty.voice import synthesize_episode
    return synthesize_episode(ep)


def _step_render(ep):
    from sty.render import render_episode
    return render_episode(ep)


def _step_stills(ep):
    from sty.render import make_stills
    return make_stills(ep)


def _step_thumbnail(ep):
    from sty.render import make_thumbnail
    return make_thumbnail(ep)


def _step_preview(ep):
    from sty.render import make_preview
    return make_preview(ep)


def _step_upload(ep, video):
    from sty.upload import upload_episode
    return upload_episode(ep, video)


RENDER_FIELDS = ["request", "stage", "release_url", "last_error", "approvals"]
UPLOAD_FIELDS = ["request", "stage", "youtube_id", "last_error"]
FAIL_FIELDS = ["request", "last_error", "youtube_id"]


def ci_run(ep: Path, what: str) -> None:
    ep = Path(ep)
    root = ep.parent.parent
    _git_sync(root)
    if load_status(ep).get("request") != what:
        print(f"{ep.name}: permintaan {what} sudah diproses, dilewati")
        return
    try:
        if what == "render":
            _step_voice(ep)
            _step_render(ep)
            _step_stills(ep)
            files = [ep / "final.mp4"]
            if (ep / "thumbnail.txt").exists():
                _step_thumbnail(ep)
                files.append(ep / "thumbnail.png")
            preview = _step_preview(ep)
            url = _release_upload(ep, files)
            _update(ep, release_url=url)
            set_stage(ep, "rendered")
            clear_request(ep, None)
            _git_publish(root, f"ci: render {ep.name}", ep, RENDER_FIELDS)
            caption = f"🎬 Udun: video {ep.name} selesai dirender. Video penuh: {url}"
            if not (preview and notify_video(preview, caption)):
                notify(caption)
        else:
            video = _release_download(ep)
            _step_upload(ep, video)
            clear_request(ep, None)
            _git_publish(root, f"ci: upload {ep.name}", ep, UPLOAD_FIELDS)
    except Exception as e:
        try:
            clear_request(ep, f"{type(e).__name__}: {e}"[:1000])
            _git_publish(root, f"ci: {what} {ep.name} gagal", ep, FAIL_FIELDS)
        except Exception as e2:
            print(f"::warning::status gagal disimpan setelah error: {type(e2).__name__}: {e2}")
        first = str(e).splitlines()[0][:300] if str(e) else type(e).__name__
        notify(f"❌ {ep.name}: {what} gagal: {first}")
        raise


def ci_fail(ep: Path, reason: str) -> None:
    """Dipanggil workflow saat job gagal/dibatalkan/timeout di luar ci_run. Membersihkan permintaan yang macet."""
    ep = Path(ep)
    root = ep.parent.parent
    try:
        _git_sync(root)
    except Exception as e:
        print(f"::warning::git pull gagal: {e}")
    st = load_status(ep)
    if not st.get("request"):
        print(f"{ep.name}: permintaan sudah dibersihkan, tidak ada yang perlu dilakukan")
        return
    what = st["request"]
    clear_request(ep, reason[:1000])
    try:
        _git_publish(root, f"ci: {what} {ep.name} dibatalkan", ep, FAIL_FIELDS)
    finally:
        notify(f"❌ {ep.name}: {what} berhenti ({reason}). Cek tab Actions di GitHub, lalu minta ulang lewat Handur.")


def register(sub) -> None:
    p = sub.add_parser("ci-pending", help="daftar permintaan tertunda (JSON)")
    p.add_argument("--root", default=str(PROJECT_ROOT))
    p.set_defaults(func=lambda a: print(json.dumps([{"episode": d.name, "request": r} for d, r in pending_requests(a.root)])))

    p = sub.add_parser("ci-run", help="jalankan permintaan render/upload (dipakai GitHub Actions)")
    p.add_argument("ep")
    p.add_argument("what", choices=["render", "upload"])
    p.add_argument("--root", default=str(PROJECT_ROOT))
    p.set_defaults(func=lambda a: ci_run(episode_dir(a.ep, a.root), a.what))

    p = sub.add_parser("ci-fail", help="bersihkan permintaan yang macet setelah job gagal/dibatalkan")
    p.add_argument("ep")
    p.add_argument("reason", nargs="?", default="job GitHub Actions gagal, dibatalkan, atau timeout")
    p.add_argument("--root", default=str(PROJECT_ROOT))
    p.set_defaults(func=lambda a: ci_fail(episode_dir(a.ep, a.root), a.reason))

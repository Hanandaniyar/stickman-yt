"""Pembantu GitHub Actions: cari permintaan tertunda, jalankan, dan laporkan hasilnya."""
import json
import subprocess
from pathlib import Path

from sty.config import PROJECT_ROOT
from sty.episode import _update, episode_dir, episodes_root, load_status, set_stage
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


def _git_sync(root: Path) -> None:
    _sh(["git", "pull", "--rebase", "--autostash"], cwd=root)


def _git_publish(root: Path, msg: str) -> None:
    _sh(["git", "add", "-A", "episodes"], cwd=root)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root).returncode == 0:
        return
    _sh(["git", "commit", "-m", msg], cwd=root)
    for _ in range(3):
        if subprocess.run(["git", "push"], cwd=root).returncode == 0:
            return
        _sh(["git", "pull", "--rebase"], cwd=root)
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
            _git_publish(root, f"ci: render {ep.name}")
            caption = f"🎬 Udun: video {ep.name} selesai dirender. Video penuh: {url}"
            if not (preview and notify_video(preview, caption)):
                notify(caption)
        else:
            video = _release_download(ep)
            _step_upload(ep, video)
            clear_request(ep, None)
            _git_publish(root, f"ci: upload {ep.name}")
    except Exception as e:
        clear_request(ep, f"{type(e).__name__}: {e}"[:1000])
        try:
            _git_publish(root, f"ci: {what} {ep.name} gagal")
        finally:
            notify(f"❌ {ep.name}: {what} gagal: {str(e).splitlines()[0][:300] if str(e) else type(e).__name__}")
        raise


def register(sub) -> None:
    p = sub.add_parser("ci-pending", help="daftar permintaan tertunda (JSON)")
    p.add_argument("--root", default=str(PROJECT_ROOT))
    p.set_defaults(func=lambda a: print(json.dumps([{"episode": d.name, "request": r} for d, r in pending_requests(a.root)])))

    p = sub.add_parser("ci-run", help="jalankan permintaan render/upload (dipakai GitHub Actions)")
    p.add_argument("ep")
    p.add_argument("what", choices=["render", "upload"])
    p.add_argument("--root", default=str(PROJECT_ROOT))
    p.set_defaults(func=lambda a: ci_run(episode_dir(a.ep, a.root), a.what))

"""Pembantu GitHub Actions: cari permintaan tertunda dan bersihkan setelah diproses."""
import json
from pathlib import Path

from sty.config import PROJECT_ROOT
from sty.episode import _update, episodes_root, load_status


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


def register(sub) -> None:
    p = sub.add_parser("ci-pending", help="daftar permintaan tertunda (JSON)")
    p.add_argument("--root", default=str(PROJECT_ROOT))

    def run(a):
        print(json.dumps([{"episode": d.name, "request": r} for d, r in pending_requests(a.root)]))

    p.set_defaults(func=run)

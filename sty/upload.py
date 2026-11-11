"""Upload video ke YouTube lewat YouTube Data API v3 (kredensial dari GitHub Secrets)."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from sty.config import load_config
from sty.episode import _update, load_status, set_stage
from sty.notify import notify

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
ET = ZoneInfo("America/New_York")
GUIDE = "docs/setup/youtube.md"


def credentials_from_env():
    from google.oauth2.credentials import Credentials

    env = {k: os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")}
    missing = [k for k, v in env.items() if not v]
    if missing:
        raise RuntimeError(f"secret YouTube belum diisi: {', '.join(missing)} (lihat {GUIDE})")
    return Credentials(
        None, refresh_token=env["YT_REFRESH_TOKEN"], client_id=env["YT_CLIENT_ID"],
        client_secret=env["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token", scopes=SCOPES,
    )


def _service():
    from googleapiclient.discovery import build

    return build("youtube", "v3", credentials=credentials_from_env(), cache_discovery=False)


def _reasons(err: HttpError) -> list[str]:
    try:
        return [e.get("reason", "") for e in json.loads(err.content)["error"]["errors"]]
    except Exception:
        return []


def _status_block(cfg: dict, now: datetime) -> dict:
    status = {"privacyStatus": cfg["upload_privacy"], "selfDeclaredMadeForKids": False}
    hour = cfg.get("publish_at_hour_et")
    if cfg["upload_privacy"] == "public" and hour is not None:
        day = now.astimezone(ET).date() + timedelta(days=1)
        at = datetime(day.year, day.month, day.day, int(hour), 0, tzinfo=ET)
        status.update(privacyStatus="private", publishAt=at.isoformat())
    return status


def upload_episode(ep: Path, video: Path, service=None, now: datetime | None = None) -> str:
    from googleapiclient.http import MediaFileUpload

    ep = Path(ep)
    if not load_status(ep)["approvals"]["final"]:
        raise PermissionError("upload butuh persetujuan akhir pemilik")
    meta = json.loads((ep / "04-metadata.json").read_text())
    if len(meta["title"]) > 100:
        raise ValueError(f"judul {len(meta['title'])} karakter; maksimal 100")
    if len(meta.get("description", "")) > 5000:
        raise ValueError("deskripsi lebih dari 5000 karakter")
    cfg = load_config()
    body = {
        "snippet": {"title": meta["title"], "description": meta.get("description", ""), "tags": meta.get("tags", []),
                    "categoryId": str(meta.get("category_id", "27"))},
        "status": _status_block(cfg, now or datetime.now(ET)),
    }
    try:
        service = service or _service()
        req = service.videos().insert(part="snippet,status", body=body,
                                      media_body=MediaFileUpload(str(video), mimetype="video/mp4", chunksize=-1, resumable=True))
        response = None
        while response is None:
            _, response = req.next_chunk()
    except HttpError as e:
        if {"quotaExceeded", "uploadLimitExceeded"} & set(_reasons(e)):
            raise RuntimeError("kuota YouTube habis, coba lagi besok") from None
        raise RuntimeError(f"YouTube menolak upload (HTTP {e.resp.status}): {', '.join(_reasons(e)) or e}") from None
    except RefreshError:
        raise RuntimeError(f"refresh token kedaluwarsa atau dicabut: buat ulang mengikuti {GUIDE}") from None

    vid = response["id"]
    thumb = ep / "thumbnail.png"
    if thumb.exists():
        try:
            service.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb), mimetype="image/png")).execute()
        except HttpError as e:
            print(f"peringatan: thumbnail gagal dipasang (HTTP {e.resp.status}); verifikasi telepon channel dulu ({GUIDE})")
    _update(ep, youtube_id=vid)
    set_stage(ep, "done")
    privacy = body["status"]["privacyStatus"] + (f", tayang {body['status']['publishAt']}" if "publishAt" in body["status"] else "")
    notify(f'📤 Udon: "{meta["title"]}" terunggah ({privacy}) https://youtu.be/{vid}')
    return vid


def register(sub) -> None:
    from sty.config import PROJECT_ROOT
    from sty.episode import episode_dir

    p = sub.add_parser("upload", help="upload video ke YouTube")
    p.add_argument("ep")
    p.add_argument("--video", required=True)
    p.add_argument("--root", default=str(PROJECT_ROOT))
    p.set_defaults(func=lambda a: print(upload_episode(episode_dir(a.ep, a.root), Path(a.video))))

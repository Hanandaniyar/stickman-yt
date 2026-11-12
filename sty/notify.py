"""Notifikasi Telegram. Tidak pernah melempar exception dan tidak pernah mencetak token."""
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

API = "https://api.telegram.org/bot{token}/{method}"
MAX_VIDEO_BYTES = 49 * 1024 * 1024
TIMEOUT = 10
LABEL = "📺 YT · "  # semua pesan dari pipeline ini milik YouTube; TikTok diberi label 🎵 TIKTOK oleh Handur

_last_error = ""


def _creds() -> tuple[str, str]:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(), os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def _call(token: str, method: str, data: bytes, content_type: str, timeout: int = TIMEOUT) -> dict | None:
    global _last_error
    req = urllib.request.Request(API.format(token=token, method=method), data=data, headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        _last_error = f"HTTP {e.code}"
    except Exception as e:  # jaringan, timeout, JSON rusak
        _last_error = type(e).__name__
    return None


def notify(text: str) -> bool:
    global _last_error
    token, chat = _creds()
    if not token or not chat:
        _last_error = "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID belum diisi"
        return False
    data = urllib.parse.urlencode({"chat_id": chat, "text": LABEL + text}).encode()
    return _call(token, "sendMessage", data, "application/x-www-form-urlencoded") is not None


def notify_video(path: Path, caption: str) -> bool:
    global _last_error
    token, chat = _creds()
    path = Path(path)
    if not token or not chat:
        _last_error = "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID belum diisi"
        return False
    if not path.exists() or path.stat().st_size > MAX_VIDEO_BYTES:
        _last_error = "video tidak ada atau lebih dari 49 MB"
        return False
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in (("chat_id", chat), ("caption", LABEL + caption), ("supports_streaming", "true")):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="video"; filename="{path.name}"\r\n'
        f"Content-Type: video/mp4\r\n\r\n".encode()
    )
    body = b"".join(parts) + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    return _call(token, "sendVideo", body, f"multipart/form-data; boundary={boundary}", timeout=120) is not None


def extract_notify_lines(commit_message: str) -> list[str]:
    return [line.strip()[len("notify:"):].strip() for line in commit_message.splitlines() if line.strip().startswith("notify:")]


def find_chat_id(token: str) -> str | None:
    resp = _call(token, "getUpdates", b"", "application/x-www-form-urlencoded")
    if not resp:
        return None
    for update in reversed(resp.get("result", [])):
        msg = update.get("message") or update.get("channel_post") or {}
        if "chat" in msg:
            return str(msg["chat"]["id"])
    return None


def _report(ok: bool) -> int:
    print("terkirim" if ok else f"tidak terkirim: {_last_error}")
    return 0


def _cmd_notify(args) -> int:
    return _report(notify(args.text))


def _cmd_notify_commit(args) -> int:
    try:
        msg = subprocess.run(["git", "log", "-1", "--format=%B"], capture_output=True, text=True, check=True).stdout
    except Exception:
        print("tidak terkirim: gagal membaca pesan commit")
        return 0
    lines = extract_notify_lines(msg)
    if not lines:
        print("tidak ada baris notify")
        return 0
    return _report(notify("\n".join(lines)))


def _cmd_find_chat_id(args) -> int:
    token, _ = _creds()
    chat = find_chat_id(token) if token else None
    print(chat if chat else "chat ID belum ditemukan: kirim pesan ke bot dulu, lalu jalankan lagi")
    return 0


def register(sub) -> None:
    p = sub.add_parser("notify", help="kirim pesan Telegram")
    p.add_argument("text")
    p.set_defaults(func=_cmd_notify)
    sub.add_parser("notify-commit", help="teruskan baris notify: dari commit terakhir").set_defaults(func=_cmd_notify_commit)
    sub.add_parser("find-chat-id", help="cari chat ID dari pesan terakhir ke bot").set_defaults(func=_cmd_find_chat_id)

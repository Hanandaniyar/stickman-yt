"""Upload video ke kotak masuk TikTok pemilik sebagai draft (Content Posting API, Upload).

Login sekali dengan `sty tiktok-login` (browser + localhost), token disimpan di
~/.config/handur/tiktok_token.json (di luar repo). Kunci aplikasi dibaca dari .env.
Tidak pernah mencetak token atau secret.
"""
import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from sty.config import PROJECT_ROOT

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
SCOPES = "user.info.basic,video.upload"
PORT = 8765
REDIRECT_URI = f"http://localhost:{PORT}/callback/"
TOKEN_FILE = Path.home() / ".config" / "handur" / "tiktok_token.json"
MAX_SINGLE_CHUNK = 64 * 1024 * 1024


class TikTokError(RuntimeError):
    pass


def load_keys(env_file: Path | None = None) -> tuple[str, str]:
    key, secret = os.environ.get("TIKTOK_CLIENT_KEY", ""), os.environ.get("TIKTOK_CLIENT_SECRET", "")
    env_file = env_file or PROJECT_ROOT / ".env"
    if (not key or not secret) and env_file.exists():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            name, value = name.strip(), value.strip().strip('"').strip("'")
            if name == "TIKTOK_CLIENT_KEY" and not key:
                key = value
            elif name == "TIKTOK_CLIENT_SECRET" and not secret:
                secret = value
    if not key or not secret:
        raise TikTokError("TIKTOK_CLIENT_KEY/TIKTOK_CLIENT_SECRET belum diisi di .env")
    return key, secret


def pkce_pair() -> tuple[str, str]:
    """TikTok desktop: code_challenge = SHA256(verifier) dalam hex (bukan base64url)."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    verifier = "".join(secrets.choice(alphabet) for _ in range(64))
    return verifier, hashlib.sha256(verifier.encode()).hexdigest()


def auth_url(client_key: str, state: str, challenge: str) -> str:
    q = {
        "client_key": client_key, "scope": SCOPES, "redirect_uri": REDIRECT_URI, "state": state,
        "response_type": "code", "code_challenge": challenge, "code_challenge_method": "S256",
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(q)


def _post(url: str, data: bytes, headers: dict, opener=urllib.request.urlopen) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with opener(req, timeout=60) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read() or b"{}")
        except Exception:
            body = {}
        err = body.get("error") or {}
        msg = err.get("message") if isinstance(err, dict) else body.get("error_description") or err
        raise TikTokError(f"HTTP {e.code}: {msg or 'tanpa keterangan'}") from None


def _token_request(params: dict, opener=urllib.request.urlopen) -> dict:
    body = _post(TOKEN_URL, urllib.parse.urlencode(params).encode(),
                 {"Content-Type": "application/x-www-form-urlencoded"}, opener)
    if "access_token" not in body:
        raise TikTokError(f"gagal mengambil token: {body.get('error_description') or body.get('error') or 'tanpa keterangan'}")
    now = int(time.time())
    return {
        "access_token": body["access_token"], "refresh_token": body.get("refresh_token", ""),
        "open_id": body.get("open_id", ""), "scope": body.get("scope", ""),
        "expires_at": now + int(body.get("expires_in", 0)),
        "refresh_expires_at": now + int(body.get("refresh_expires_in", 0)),
    }


def save_token(tok: dict, path: Path = TOKEN_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tok))
    path.chmod(0o600)


def access_token(path: Path = TOKEN_FILE, opener=urllib.request.urlopen, now=None) -> str:
    if not path.exists():
        raise TikTokError("belum login TikTok: jalankan `uv run sty tiktok-login`")
    tok = json.loads(path.read_text())
    now = now or int(time.time())
    if tok.get("expires_at", 0) - 300 > now:
        return tok["access_token"]
    if not tok.get("refresh_token") or tok.get("refresh_expires_at", 0) <= now:
        raise TikTokError("login TikTok kedaluwarsa: jalankan `uv run sty tiktok-login`")
    key, secret = load_keys()
    new = _token_request({"client_key": key, "client_secret": secret, "grant_type": "refresh_token",
                          "refresh_token": tok["refresh_token"]}, opener)
    save_token(new, path)
    return new["access_token"]


def login(open_browser=webbrowser.open) -> str:
    key, secret = load_keys()
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(16)
    result: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            url = urllib.parse.urlparse(self.path)
            if not url.path.startswith("/callback"):
                self.send_response(404)
                self.end_headers()
                return
            q = urllib.parse.parse_qs(url.query)
            result.update({k: v[0] for k, v in q.items()})
            ok = "code" in result and result.get("state") == state
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "Login TikTok berhasil. Tab ini boleh ditutup." if ok else "Login TikTok gagal. Kembali ke Claude."
            self.wfile.write(f"<h2>{msg}</h2>".encode())

        def log_message(self, *a):
            pass

    server = HTTPServer(("localhost", PORT), Handler)
    server.timeout = 5
    open_browser(auth_url(key, state, challenge))
    print("Browser dibuka untuk login TikTok. Menunggu (maks 5 menit)...")
    deadline = time.time() + 300
    while "code" not in result and "error" not in result:
        if time.time() > deadline:
            server.server_close()
            raise TikTokError("waktu login habis")
        server.handle_request()
    server.server_close()
    if result.get("state") != state:
        raise TikTokError("state tidak cocok, login dibatalkan")
    if "error" in result:
        raise TikTokError(f"login ditolak: {result.get('error_description') or result['error']}")
    tok = _token_request({"client_key": key, "client_secret": secret, "code": result["code"],
                          "grant_type": "authorization_code", "redirect_uri": REDIRECT_URI,
                          "code_verifier": verifier})
    save_token(tok)
    return tok.get("scope", "")


def upload_draft(video: Path, opener=urllib.request.urlopen, token: str | None = None) -> str:
    video = Path(video)
    if not video.exists():
        raise TikTokError(f"video tidak ditemukan: {video}")
    size = video.stat().st_size
    if size > MAX_SINGLE_CHUNK:
        raise TikTokError("video lebih dari 64 MB; perkecil dulu")
    token = token or access_token(opener=opener)
    body = {"source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}}
    res = _post(INIT_URL, json.dumps(body).encode(),
                {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"}, opener)
    data = res.get("data") or {}
    if not data.get("upload_url"):
        raise TikTokError(f"init upload gagal: {(res.get('error') or {}).get('message', 'tanpa keterangan')}")
    req = urllib.request.Request(data["upload_url"], data=video.read_bytes(), method="PUT", headers={
        "Content-Type": "video/mp4", "Content-Length": str(size), "Content-Range": f"bytes 0-{size - 1}/{size}",
    })
    try:
        with opener(req, timeout=300):
            pass
    except urllib.error.HTTPError as e:
        raise TikTokError(f"kirim file gagal: HTTP {e.code}") from None
    return data["publish_id"]


def status(publish_id: str, opener=urllib.request.urlopen) -> str:
    res = _post(STATUS_URL, json.dumps({"publish_id": publish_id}).encode(),
                {"Authorization": f"Bearer {access_token(opener=opener)}", "Content-Type": "application/json; charset=UTF-8"},
                opener)
    data = res.get("data") or {}
    return data.get("status", "") + (f" ({data['fail_reason']})" if data.get("fail_reason") else "")


def _run(fn) -> int:
    try:
        print(fn())
        return 0
    except TikTokError as e:
        print(f"gagal: {e}")
        return 1


def register(sub) -> None:
    sub.add_parser("tiktok-login", help="login TikTok sekali (simpan token lokal)").set_defaults(
        func=lambda a: _run(lambda: f"login berhasil, scope: {login()}"))
    p = sub.add_parser("tiktok-upload", help="kirim video ke kotak masuk TikTok sebagai draft")
    p.add_argument("video")
    p.set_defaults(func=lambda a: _run(lambda: f"terkirim ke kotak masuk TikTok, publish_id: {upload_draft(Path(a.video))}"))
    s = sub.add_parser("tiktok-status", help="cek status upload draft")
    s.add_argument("publish_id")
    s.set_defaults(func=lambda a: _run(lambda: status(a.publish_id)))

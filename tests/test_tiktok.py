import hashlib
import io
import json
import urllib.parse

import pytest

from sty import tiktok as t


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_pkce_challenge_is_hex_sha256():
    verifier, challenge = t.pkce_pair()
    assert 43 <= len(verifier) <= 128
    assert challenge == hashlib.sha256(verifier.encode()).hexdigest()


def test_auth_url_has_required_params():
    q = urllib.parse.parse_qs(urllib.parse.urlparse(t.auth_url("KEY", "st", "ch")).query)
    assert q["client_key"] == ["KEY"]
    assert q["redirect_uri"] == ["http://localhost:8765/callback/"]
    assert q["scope"] == ["user.info.basic,video.upload"]
    assert q["code_challenge_method"] == ["S256"]


def test_load_keys_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("TIKTOK_CLIENT_KEY", raising=False)
    monkeypatch.delenv("TIKTOK_CLIENT_SECRET", raising=False)
    env = tmp_path / ".env"
    env.write_text("# x\nTIKTOK_CLIENT_KEY=abc\nTIKTOK_CLIENT_SECRET='s3'\n")
    assert t.load_keys(env) == ("abc", "s3")


def test_load_keys_missing_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("TIKTOK_CLIENT_KEY", raising=False)
    monkeypatch.delenv("TIKTOK_CLIENT_SECRET", raising=False)
    (tmp_path / ".env").write_text("TIKTOK_CLIENT_KEY=\n")
    with pytest.raises(t.TikTokError):
        t.load_keys(tmp_path / ".env")


def test_access_token_valid_is_reused(tmp_path):
    f = tmp_path / "tok.json"
    t.save_token({"access_token": "A", "expires_at": 10_000, "refresh_token": "R", "refresh_expires_at": 99_999}, f)
    assert t.access_token(f, opener=lambda *a, **k: pytest.fail("no network"), now=1_000) == "A"
    assert oct(f.stat().st_mode)[-3:] == "600"


def test_access_token_missing_file(tmp_path):
    with pytest.raises(t.TikTokError, match="tiktok-login"):
        t.access_token(tmp_path / "none.json")


def test_upload_draft_single_chunk(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"x" * 1000)
    calls = []

    def opener(req, timeout=0):
        calls.append(req)
        if req.get_method() == "POST":
            return Resp(json.dumps({"data": {"upload_url": "https://up.example/u", "publish_id": "p1"}}).encode())
        return Resp(b"")

    assert t.upload_draft(video, opener=opener, token="T") == "p1"
    init = json.loads(calls[0].data)
    assert init["source_info"] == {"source": "FILE_UPLOAD", "video_size": 1000, "chunk_size": 1000, "total_chunk_count": 1}
    assert calls[0].get_header("Authorization") == "Bearer T"
    assert calls[1].get_method() == "PUT"
    assert calls[1].get_header("Content-range") == "bytes 0-999/1000"


def test_upload_draft_missing_video(tmp_path):
    with pytest.raises(t.TikTokError):
        t.upload_draft(tmp_path / "nope.mp4", token="T")

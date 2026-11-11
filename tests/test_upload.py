import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httplib2
import pytest
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from sty import upload as up
from sty.episode import approve, create_episode, load_status

ET = ZoneInfo("America/New_York")


def http_error(status, reason):
    content = json.dumps({"error": {"errors": [{"reason": reason}], "message": reason}}).encode()
    return HttpError(httplib2.Response({"status": status}), content)


class FakeService:
    def __init__(self, insert_error=None, thumb_error=None):
        self.body = None
        self.thumb_called = False
        self.insert_error, self.thumb_error = insert_error, thumb_error

    def videos(self):
        svc = self

        class V:
            def insert(self, part, body, media_body):
                svc.body = body

                class Req:
                    def next_chunk(self):
                        if svc.insert_error:
                            raise svc.insert_error
                        return None, {"id": "abc123"}

                return Req()

        return V()

    def thumbnails(self):
        svc = self

        class T:
            def set(self, videoId, media_body):
                class Req:
                    def execute(self):
                        svc.thumb_called = True
                        if svc.thumb_error:
                            raise svc.thumb_error
                        return {}

                return Req()

        return T()


@pytest.fixture
def ep(tmp_path, monkeypatch):
    ep = create_episode("x", tmp_path)
    (ep / "04-metadata.json").write_text(json.dumps({
        "title": "Why Inflation Eats Your Savings", "description": "Sources...", "tags": ["inflation", "money"],
        "category_id": "27"}))
    (ep / "final.mp4").write_bytes(b"\x00" * 100)
    (ep / "thumbnail.png").write_bytes(b"\x89PNG")
    monkeypatch.setattr(up, "notify", lambda t: True)
    monkeypatch.setattr(up, "load_config", lambda: {"upload_privacy": "private", "publish_at_hour_et": None})
    return ep


def test_requires_final_approval(ep):
    with pytest.raises(PermissionError, match="butuh persetujuan akhir"):
        up.upload_episode(ep, ep / "final.mp4", service=FakeService())


def test_insert_body(ep):
    approve(ep, "final")
    svc = FakeService()
    assert up.upload_episode(ep, ep / "final.mp4", service=svc) == "abc123"
    assert svc.body["snippet"]["title"] == "Why Inflation Eats Your Savings"
    assert svc.body["snippet"]["tags"] == ["inflation", "money"]
    assert svc.body["snippet"]["categoryId"] == "27"
    assert svc.body["status"]["privacyStatus"] == "private"
    assert svc.body["status"]["selfDeclaredMadeForKids"] is False
    st = load_status(ep)
    assert st["youtube_id"] == "abc123" and st["stage"] == "done"
    assert svc.thumb_called


def test_scheduled_publish(ep, monkeypatch):
    approve(ep, "final")
    monkeypatch.setattr(up, "load_config", lambda: {"upload_privacy": "public", "publish_at_hour_et": 9})
    svc = FakeService()
    up.upload_episode(ep, ep / "final.mp4", service=svc, now=datetime(2026, 11, 12, 15, 0, tzinfo=ET))
    st = svc.body["status"]
    assert st["privacyStatus"] == "private"
    at = datetime.fromisoformat(st["publishAt"].replace("Z", "+00:00")).astimezone(ET)
    assert (at.year, at.month, at.day, at.hour, at.minute) == (2026, 11, 13, 9, 0)


def test_thumbnail_403_is_warning(ep, capsys):
    approve(ep, "final")
    vid = up.upload_episode(ep, ep / "final.mp4", service=FakeService(thumb_error=http_error(403, "forbidden")))
    assert vid == "abc123" and load_status(ep)["stage"] == "done"
    assert "thumbnail" in capsys.readouterr().out


def test_quota_error(ep):
    approve(ep, "final")
    with pytest.raises(RuntimeError, match="kuota YouTube habis, coba lagi besok"):
        up.upload_episode(ep, ep / "final.mp4", service=FakeService(insert_error=http_error(403, "quotaExceeded")))
    assert load_status(ep)["stage"] != "done"


def test_invalid_grant(ep):
    approve(ep, "final")
    with pytest.raises(RuntimeError) as e:
        up.upload_episode(ep, ep / "final.mp4", service=FakeService(insert_error=RefreshError("invalid_grant")))
    assert "refresh token kedaluwarsa" in str(e.value) and "docs/setup/youtube.md" in str(e.value)


def test_title_too_long(ep):
    approve(ep, "final")
    meta = json.loads((ep / "04-metadata.json").read_text())
    meta["title"] = "x" * 101
    (ep / "04-metadata.json").write_text(json.dumps(meta))
    svc = FakeService()
    with pytest.raises(ValueError, match="100"):
        up.upload_episode(ep, ep / "final.mp4", service=svc)
    assert svc.body is None


def test_missing_env_credentials(monkeypatch):
    for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(RuntimeError, match="YT_REFRESH_TOKEN"):
        up.credentials_from_env()

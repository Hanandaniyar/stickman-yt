import urllib.error

import pytest

from sty import notify as n

TOKEN = "123456:SECRET-TOKEN-abc"


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")


def test_missing_env_returns_false_without_request(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    called = []
    monkeypatch.setattr(n.urllib.request, "urlopen", lambda *a, **k: called.append(1))
    assert n.notify("halo") is False
    assert called == []


def test_network_error_returns_false(env, monkeypatch):
    def boom(*a, **k):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(n.urllib.request, "urlopen", boom)
    assert n.notify("halo") is False


def test_extract_notify_lines():
    msg = "feat: x\n\nnotify: 👑 Handur: naskah lolos\nnotify: ✍️ Udan: selesai\nbody"
    assert n.extract_notify_lines(msg) == ["👑 Handur: naskah lolos", "✍️ Udan: selesai"]


def test_video_too_big_skipped(env, monkeypatch, tmp_path):
    big = tmp_path / "p.mp4"
    with open(big, "wb") as f:
        f.truncate(50 * 1024 * 1024)
    called = []
    monkeypatch.setattr(n.urllib.request, "urlopen", lambda *a, **k: called.append(1))
    assert n.notify_video(big, "cap") is False
    assert called == []


def test_token_not_in_output(env, monkeypatch, capsys):
    def boom(req, *a, **k):
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, None)

    monkeypatch.setattr(n.urllib.request, "urlopen", boom)
    from sty.cli import main

    assert main(["notify", "halo"]) == 0
    out = capsys.readouterr()
    assert TOKEN not in out.out + out.err
    assert "tidak terkirim" in out.out

import pytest

from sty import ci
from sty.episode import approve, create_episode, load_status, request, _update
from tests.conftest import write_scenes


class Calls:
    def __init__(self, fail_at=None):
        self.log, self.fail_at, self.notes = [], fail_at, []

    def step(self, name):
        def fn(*a, **k):
            self.log.append(name)
            if name == self.fail_at:
                raise RuntimeError(f"{name} meledak")
            return {"preview": None}.get(name)
        return fn


@pytest.fixture
def env(tmp_path, monkeypatch):
    ep = create_episode("x", tmp_path)
    write_scenes(ep, ["s01"])
    calls = Calls()

    def install(c):
        for name in ("voice", "render", "stills", "thumbnail", "preview", "upload"):
            monkeypatch.setattr(ci, f"_step_{name}", c.step(name))
        monkeypatch.setattr(ci, "_git_sync", lambda root: c.log.append("pull"))
        monkeypatch.setattr(ci, "_git_publish", lambda root, msg, *a, **k: c.log.append("push"))
        monkeypatch.setattr(ci, "_release_upload", lambda ep, files: (c.log.append("release"), "https://gh/rel/ep-001")[1])
        monkeypatch.setattr(ci, "_release_download", lambda ep: (c.log.append("download"), ep / "final.mp4")[1])
        monkeypatch.setattr(ci, "notify", lambda t: c.notes.append(t) or True)
        monkeypatch.setattr(ci, "notify_video", lambda p, cap: c.notes.append(cap) or True)

    install(calls)
    return ep, calls, install


def test_render_flow(env):
    ep, calls, _ = env
    request(ep, "render")
    ci.ci_run(ep, "render")
    assert calls.log == ["pull", "voice", "render", "stills", "preview", "release", "push"]
    st = load_status(ep)
    assert st["stage"] == "rendered" and st["request"] is None and st["release_url"] == "https://gh/rel/ep-001"
    assert any("https://gh/rel/ep-001" in n for n in calls.notes)


def test_render_includes_thumbnail_when_text_exists(env):
    ep, calls, _ = env
    (ep / "thumbnail.txt").write_text("Hi")
    request(ep, "render")
    ci.ci_run(ep, "render")
    assert "thumbnail" in calls.log


def test_skips_if_request_already_cleared(env):
    ep, calls, _ = env
    ci.ci_run(ep, "render")
    assert calls.log == ["pull"]


def test_failure_clears_request_and_notifies(env):
    ep, _, install = env
    failing = Calls(fail_at="render")
    install(failing)
    request(ep, "render")
    with pytest.raises(RuntimeError):
        ci.ci_run(ep, "render")
    st = load_status(ep)
    assert st["request"] is None and "render meledak" in st["last_error"]
    assert failing.log[-1] == "push"
    assert any(n.startswith("❌") for n in failing.notes)


def test_upload_flow(env):
    ep, calls, _ = env
    approve(ep, "final")
    _update(ep, release_url="https://gh/rel/ep-001")
    request(ep, "upload")
    ci.ci_run(ep, "upload")
    assert calls.log == ["pull", "download", "upload", "push"]
    assert load_status(ep)["request"] is None

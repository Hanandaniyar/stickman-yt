"""_git_publish memakai repo git sungguhan: harus tahan konflik dengan push lain di status.json."""
import json
import subprocess

import pytest

from sty import ci
from sty.episode import create_episode, load_status, record_review, request, _update
from tests.conftest import write_scenes


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repos(tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    runner = tmp_path / "runner"
    git(tmp_path, "clone", "-q", str(remote), str(runner))
    for k, v in (("user.name", "ci"), ("user.email", "ci@x")):
        git(runner, "config", k, v)
    ep = create_episode("x", runner)
    write_scenes(ep, ["s01"])
    request(ep, "render")
    git(runner, "add", "-A")
    git(runner, "commit", "-qm", "init")
    git(runner, "push", "-q", "origin", "main")
    owner = tmp_path / "owner"
    git(tmp_path, "clone", "-q", str(remote), str(owner))
    for k, v in (("user.name", "owner"), ("user.email", "o@x")):
        git(owner, "config", k, v)
    return runner, owner, ep


def test_publish_survives_conflicting_status_push(repos):
    runner, owner, ep = repos
    # Pemilik/Handur mencatat review selama render berjalan, lalu push.
    owner_ep = owner / "episodes" / ep.name
    record_review(owner_ep, "scenes", "LOLOS", "ok")
    git(owner, "commit", "-qam", "review")
    git(owner, "push", "-q")
    # CI selesai render: menulis file baru dan mengubah status.
    (ep / "timing.json").write_text("{}")
    _update(ep, request=None, stage="rendered", release_url="https://rel")
    ci._git_publish(runner, "ci: render", ep, ["request", "stage", "release_url", "last_error"])
    git(owner, "pull", "-q")
    st = load_status(owner_ep)
    assert st["request"] is None and st["stage"] == "rendered" and st["release_url"] == "https://rel"
    assert len(st["reviews"]) == 1  # review pemilik tidak hilang
    assert (owner_ep / "timing.json").exists()


def test_ci_fail_clears_stuck_request_and_notifies(repos, monkeypatch):
    runner, _, ep = repos
    notes = []
    monkeypatch.setattr(ci, "notify", lambda t: notes.append(t) or True)
    ci.ci_fail(ep, "job dibatalkan atau timeout")
    st = load_status(ep)
    assert st["request"] is None and "timeout" in st["last_error"]
    assert notes and notes[0].startswith("❌")
    assert "request" not in json.loads(git(runner, "show", "origin/main:episodes/" + ep.name + "/status.json")) or \
        json.loads(git(runner, "show", "origin/main:episodes/" + ep.name + "/status.json"))["request"] is None


def test_ci_fail_noop_when_already_handled(repos, monkeypatch):
    runner, _, ep = repos
    _update(ep, request=None, last_error="sudah ditangani")
    git(runner, "commit", "-qam", "handled")
    git(runner, "push", "-q")
    notes = []
    monkeypatch.setattr(ci, "notify", lambda t: notes.append(t) or True)
    ci.ci_fail(ep, "x")
    assert notes == [] and load_status(ep)["last_error"] == "sudah ditangani"


def test_failure_notifies_even_if_status_unreadable(repos, monkeypatch):
    runner, _, ep = repos
    notes = []
    monkeypatch.setattr(ci, "notify", lambda t: notes.append(t) or True)
    monkeypatch.setattr(ci, "_step_voice", lambda e: (_ for _ in ()).throw(RuntimeError("tts mati")))

    def broken_publish(*a, **k):
        raise RuntimeError("push ditolak")

    monkeypatch.setattr(ci, "_git_publish", broken_publish)
    monkeypatch.setattr(ci, "clear_request", lambda *a: json.loads("<<<<<<< konflik"))
    with pytest.raises(RuntimeError):
        ci.ci_run(ep, "render")
    assert any("tts mati" in n for n in notes)

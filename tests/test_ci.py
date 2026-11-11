import json

from sty.ci import clear_request, pending_requests
from sty.episode import create_episode, load_status, request
from tests.conftest import write_scenes


def test_pending_requests_lists_only_requested(tmp_path):
    a = create_episode("a", tmp_path)
    create_episode("b", tmp_path)
    write_scenes(a, ["s01"])
    request(a, "render")
    assert pending_requests(tmp_path) == [(a, "render")]


def test_clear_request_records_error(tmp_path):
    a = create_episode("a", tmp_path)
    write_scenes(a, ["s01"])
    request(a, "render")
    clear_request(a, "render gagal")
    st = load_status(a)
    assert st["request"] is None and st["last_error"] == "render gagal"


def test_ci_pending_cli_json(tmp_path, capsys, monkeypatch):
    a = create_episode("a", tmp_path)
    write_scenes(a, ["s01"])
    request(a, "render")
    from sty.cli import main

    assert main(["ci-pending", "--root", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out) == [{"episode": a.name, "request": "render"}]

from pathlib import Path

import yaml

WF = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def _pipeline():
    return yaml.safe_load((WF / "pipeline.yml").read_text())


def test_work_has_concurrency_per_episode():
    work = _pipeline()["jobs"]["work"]
    assert "matrix.episode" in work["concurrency"]["group"]
    assert work["concurrency"]["cancel-in-progress"] is False
    assert work["timeout-minutes"] == 120


def test_permissions_contents_write():
    assert _pipeline()["permissions"]["contents"] == "write"


def test_secrets_only_in_needed_steps():
    for job_name, job in _pipeline()["jobs"].items():
        for step in job.get("steps", []):
            env = " ".join(str(v) for v in (step.get("env") or {}).values())
            text = yaml.safe_dump(step)
            if "YT_REFRESH_TOKEN" in text:
                assert "upload" in step.get("name", "").lower(), (job_name, step.get("name"))
    assert "secrets." not in yaml.safe_dump(_pipeline()["jobs"]["plan"])


def test_matrix_values_not_inlined_into_shell():
    for job in _pipeline()["jobs"].values():
        for step in job.get("steps", []):
            assert "${{ matrix" not in str(step.get("run", "")), step.get("name")


def test_no_forbidden_hyperframes_commands():
    forbidden = ["cloud render", "auth login", "hyperframes lambda", "hyperframes cloudrun",
                 "media-use generate", "hyperframes feedback", "hyperframes publish"]
    for wf in WF.glob("*.yml"):
        text = wf.read_text()
        for bad in forbidden:
            assert bad not in text, (wf.name, bad)


def test_cleanup_step_runs_on_failure_or_cancel():
    steps = _pipeline()["jobs"]["work"]["steps"]
    last = steps[-1]
    assert "failure()" in last["if"] and "cancelled()" in last["if"]
    assert "sty ci-fail" in last["run"]


def test_triggers_on_main_and_claude_branches():
    on = _pipeline()[True] if True in _pipeline() else _pipeline()["on"]
    assert set(on["push"]["branches"]) == {"main", "claude/**"}

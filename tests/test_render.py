import json
from pathlib import Path

import pytest

from sty import render as r
from sty.episode import create_episode
from tests.conftest import write_scenes
from tests.test_build import _timing


class FakeRun:
    def __init__(self, duration=4.0, fail=None, preview_bytes=1000):
        self.calls, self.duration, self.fail, self.preview_bytes = [], duration, fail, preview_bytes

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        res = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        name = " ".join(cmd)
        if self.fail and self.fail in name:
            res.returncode = 1
            res.stderr = "\n".join(f"line {i}" for i in range(30))
            return res
        if "ffprobe" in cmd[0]:
            res.stdout = f"{self.duration}\n"
        elif "render" in cmd:
            Path(cmd[cmd.index("-o") + 1]).write_bytes(b"mp4")
        elif cmd[0] == "ffmpeg":
            out = Path(cmd[-1])
            with open(out, "wb") as f:
                f.truncate(self.preview_bytes)
        elif "snapshot" in cmd:
            d = Path(cmd[cmd.index("-o") + 1])
            d.mkdir(parents=True, exist_ok=True)
            (d / "frame-00-at-0s.png").write_bytes(b"png")
        return res

    def names(self):
        return [" ".join(c) for c in self.calls]


@pytest.fixture
def ep(tmp_path):
    ep = create_episode("x", tmp_path)
    write_scenes(ep, ["s01", "s02"])
    _timing(ep, [("s01", 0.0, 1.0), ("s02", 1.25, 3.0)])
    return ep


def test_lint_runs_before_render(ep):
    run = FakeRun()
    out = r.render_episode(ep, run=run)
    names = run.names()
    lint = next(i for i, n in enumerate(names) if " lint " in f" {n} ")
    rend = next(i for i, n in enumerate(names) if " render " in f" {n} ")
    assert lint < rend and out == ep / "final.mp4"
    assert "--quality delivery" in names[rend] and "--strict" in names[rend]


def test_duration_mismatch_raises(ep):
    with pytest.raises(RuntimeError, match="durasi"):
        r.render_episode(ep, run=FakeRun(duration=2.0))


def test_render_failure_includes_stderr_tail(ep):
    with pytest.raises(RuntimeError) as e:
        r.render_episode(ep, run=FakeRun(fail="render"))
    assert "line 29" in str(e.value) and "line 5\n" not in str(e.value)


def test_preview_too_big_returns_none(ep):
    (ep / "final.mp4").write_bytes(b"mp4")
    assert r.make_preview(ep, run=FakeRun(preview_bytes=50 * 1024 * 1024)) is None
    assert not (ep / "preview.mp4").exists()


def test_preview_ok(ep):
    (ep / "final.mp4").write_bytes(b"mp4")
    assert r.make_preview(ep, run=FakeRun()) == ep / "preview.mp4"


def test_stills_at_expected_times(ep):
    run = FakeRun()
    r.make_stills(ep, run=run)
    snap = next(c for c in run.calls if "snapshot" in c)
    assert snap[snap.index("--at") + 1] == "1,1,2,3,3"  # 4.0s video: 1s, 25%, 50%, 75%, end-1s


def test_thumbnail_fills_template(ep):
    (ep / "thumbnail.txt").write_text("Inflation <Ate> Savings\npose: shrug\n")
    run = FakeRun()
    out = r.make_thumbnail(ep, run=run)
    html = (ep / "build" / "thumb" / "index.html").read_text()
    assert "Inflation &lt;Ate&gt; Savings" in html and 'pose: "shrug"' in html
    assert out == ep / "thumbnail.png" and out.exists()


def test_thumbnail_rejects_unknown_pose(ep):
    (ep / "thumbnail.txt").write_text("Hi\npose: dance\n")
    with pytest.raises(ValueError, match="dance"):
        r.make_thumbnail(ep, run=FakeRun())


def test_preview_keeps_vertical_shape_for_shorts(ep):
    n = json.loads((ep / "narration.json").read_text())
    n["format"] = "short"
    (ep / "narration.json").write_text(json.dumps(n))
    (ep / "final.mp4").write_bytes(b"mp4")
    run = FakeRun()
    r.make_preview(ep, run=run)
    assert "scale=480:854" in run.names()[0]


def test_preview_landscape_default(ep):
    (ep / "final.mp4").write_bytes(b"mp4")
    run = FakeRun()
    r.make_preview(ep, run=run)
    assert "scale=854:480" in run.names()[0]

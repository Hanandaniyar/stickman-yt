import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from sty.episode import create_episode
from sty.voice import SAMPLE_RATE, synthesize_episode
from tests.conftest import write_scenes


class FakeRun:
    """Meniru `npx hyperframes tts|transcribe`: wav diam 1 detik, dua kata per adegan."""

    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        out = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        if "tts" in cmd:
            text = cmd[cmd.index("tts") + 1]
            if self.fail_on and self.fail_on in text:
                out.returncode, out.stderr = 1, "kokoro crashed"
                return out
            path = Path(cmd[cmd.index("-o") + 1])
            path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(path, np.zeros(SAMPLE_RATE, dtype="float32"), SAMPLE_RATE)
        elif "transcribe" in cmd:
            d = Path(cmd[cmd.index("-d") + 1])
            tp = d / "transcript.json"
            tp.parent.mkdir(parents=True, exist_ok=True)
            tp.write_text(json.dumps([{"id": "w0", "text": "Hello", "start": 0.1, "end": 0.4},
                                      {"id": "w1", "text": "there", "start": 0.5, "end": 0.9}]))
            out.stdout = json.dumps({"ok": True, "transcriptPath": str(tp)})
        return out

    def tts_texts(self):
        return [c[c.index("tts") + 1] for c in self.calls if "tts" in c]


@pytest.fixture
def ep3(tmp_path):
    ep = create_episode("x", tmp_path)
    write_scenes(ep, ["s01", "s02", "s03"])
    return ep


def test_scene_timing(ep3):
    t = synthesize_episode(ep3, run=FakeRun())
    assert t["scenes"][1]["start"] == pytest.approx(1.25)
    assert t["duration"] == pytest.approx(3.5)
    assert json.loads((ep3 / "timing.json").read_text()) == t
    assert sf.info(str(ep3 / "audio" / "narration.wav")).duration == pytest.approx(3.5)


def test_resume_skips_existing(ep3):
    synthesize_episode(ep3, run=FakeRun())
    (ep3 / "audio" / "s02.wav").unlink()
    run = FakeRun()
    synthesize_episode(ep3, run=run)
    assert len(run.tts_texts()) == 1


def test_force_regenerates(ep3):
    synthesize_episode(ep3, run=FakeRun())
    run = FakeRun()
    synthesize_episode(ep3, run=run, force=True)
    assert len(run.tts_texts()) == 3


def test_words_offset(ep3):
    t = synthesize_episode(ep3, run=FakeRun())
    assert len(t["words"]) == 6
    assert t["words"][2] == {"w": "Hello", "start": pytest.approx(1.35), "end": pytest.approx(1.65)}


def test_normalized_text_passed_to_tts(tmp_path):
    ep = create_episode("x", tmp_path)
    write_scenes(ep, ["s01"])
    data = json.loads((ep / "narration.json").read_text())
    data["scenes"][0]["text"] = "Inflation hit 7% in 2022."
    (ep / "narration.json").write_text(json.dumps(data))
    run = FakeRun()
    synthesize_episode(ep, run=run)
    assert run.tts_texts() == ["Inflation hit seven percent in twenty twenty-two."]


def test_tts_failure_names_scene(ep3):
    data = json.loads((ep3 / "narration.json").read_text())
    data["scenes"][1]["text"] = "BOOM"
    (ep3 / "narration.json").write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match="s02"):
        synthesize_episode(ep3, run=FakeRun(fail_on="BOOM"))


def test_invalid_narration_blocks(tmp_path):
    ep = create_episode("x", tmp_path)
    run = FakeRun()
    with pytest.raises(ValueError):
        synthesize_episode(ep, run=run)
    assert run.calls == []

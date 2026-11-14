"""Narasi per adegan dengan `npx hyperframes tts` (Kokoro) dan timing kata dengan `npx hyperframes transcribe`."""
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from sty.config import load_config
from sty.episode import episode_dir, validate_narration
from sty.textnorm import normalize_for_tts

SAMPLE_RATE = 24000
WHISPER_MODEL = "small.en"
HF_ENV = {"HYPERFRAMES_NO_TELEMETRY": "1", "DO_NOT_TRACK": "1"}


def hf(*args: str) -> list[str]:
    return ["npx", "--no-install", "hyperframes", *args]


def _run(run, cmd, what):
    res = run(cmd, capture_output=True, text=True, env={**os.environ, **HF_ENV})
    if res.returncode != 0:
        out = "\n".join((res.stdout or "").splitlines()[-8:])
        err = "\n".join((res.stderr or "").splitlines()[-20:])
        raise RuntimeError(f"{what} gagal (exit {res.returncode}):\n{err}\n--- stdout ---\n{out}")
    return res


def _load_words(stdout: str) -> list[dict]:
    info = json.loads(stdout.strip().splitlines()[-1])
    data = json.loads(Path(info["transcriptPath"]).read_text())
    words = data["words"] if isinstance(data, dict) else data
    return [{"w": w["text"], "start": float(w["start"]), "end": float(w["end"])} for w in words]


def synthesize_episode(ep: Path, *, force: bool = False, run=subprocess.run) -> dict:
    ep = Path(ep)
    errs = validate_narration(ep)
    if errs:
        raise ValueError("storyboard belum valid:\n" + "\n".join(errs))
    cfg = load_config()
    scenes = json.loads((ep / "narration.json").read_text())["scenes"]
    audio = ep / "audio"
    audio.mkdir(exist_ok=True)

    chunks, timing_scenes, words, cursor, rate = [], [], [], 0.0, None
    for sc in scenes:
        sid = sc["id"]
        wav = audio / f"{sid}.wav"
        if force or not wav.exists():
            text = normalize_for_tts(sc["text"])
            try:
                _run(run, hf("tts", text, "-o", str(wav), "-v", cfg["voice"], "-s", str(cfg["voice_speed"])), f"TTS adegan {sid}")
            except RuntimeError as e:
                wav.unlink(missing_ok=True)
                raise RuntimeError(f"{sid}: {e}") from None
        data, sr = sf.read(str(wav), dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        rate = rate or sr
        if sr != rate:
            raise RuntimeError(f"{sid}: sample rate {sr} berbeda dari {rate}")
        if chunks:
            gap = np.zeros(int(round(cfg["scene_gap_s"] * rate)), dtype="float32")
            chunks.append(gap)
            cursor += len(gap) / rate
        start = cursor
        chunks.append(data)
        cursor += len(data) / rate
        timing_scenes.append({"id": sid, "start": round(start, 4), "end": round(cursor, 4)})

        tx_dir = audio / "tx" / sid
        res = _run(run, hf("transcribe", str(wav), "-d", str(tx_dir), "--model", WHISPER_MODEL, "--json"), f"transkripsi adegan {sid}")
        for w in _load_words(res.stdout):
            words.append({"w": w["w"], "start": round(start + w["start"], 4), "end": round(start + w["end"], 4)})

    sf.write(str(audio / "narration.wav"), np.concatenate(chunks), rate)
    timing = {"duration": round(cursor, 4), "scenes": timing_scenes, "words": words}
    (ep / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")
    return timing


def register(sub) -> None:
    from sty.config import PROJECT_ROOT

    p = sub.add_parser("voice", help="buat narasi Kokoro + timing kata")
    p.add_argument("ep")
    p.add_argument("--force", action="store_true")
    p.add_argument("--root", default=str(PROJECT_ROOT))

    def cmd(a):
        t = synthesize_episode(episode_dir(a.ep, a.root), force=a.force)
        print(f"narasi {t['duration']:.1f} detik, {len(t['scenes'])} adegan, {len(t['words'])} kata")

    p.set_defaults(func=cmd)

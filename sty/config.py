"""Pengaturan proyek dari config.json, digabung dengan nilai default."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "approve_topic": True,
    "approve_script": True,
    "approve_final": True,
    "max_revision_rounds": 2,
    "upload_privacy": "private",
    "publish_at_hour_et": None,
    "voice": "am_michael",
    "voice_speed": 1.0,
    "scene_gap_s": 0.25,
    "music_volume": 0.08,
}


def load_config(root: Path = PROJECT_ROOT) -> dict:
    cfg = dict(DEFAULTS)
    path = Path(root) / "config.json"
    if path.exists():
        data = json.loads(path.read_text())
        unknown = sorted(set(data) - set(DEFAULTS))
        if unknown:
            raise ValueError(f"key tidak dikenal di config.json: {', '.join(unknown)}")
        cfg.update(data)
    return cfg

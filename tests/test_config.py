import json

import pytest

from sty.config import load_config


def test_defaults_when_file_missing(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg["max_revision_rounds"] == 2
    assert cfg["upload_privacy"] == "private"


def test_file_overrides(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"approve_topic": False}))
    cfg = load_config(tmp_path)
    assert cfg["approve_topic"] is False
    assert cfg["approve_script"] is True


def test_unknown_key_rejected(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"aproove": True}))
    with pytest.raises(ValueError, match="aproove"):
        load_config(tmp_path)

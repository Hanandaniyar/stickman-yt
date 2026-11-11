import json

import pytest

from sty.episode import create_episode


@pytest.fixture
def ep(tmp_path):
    return create_episode("Why Inflation", tmp_path)


def write_scenes(ep, ids, music=None):
    (ep / "narration.json").write_text(
        json.dumps({"scenes": [{"id": i, "text": f"Narration for {i}."} for i in ids], "music": music})
    )
    for i in ids:
        (ep / "scenes" / f"{i}.html").write_text(f'<section data-scene="{i}"><p>{i}</p></section>')

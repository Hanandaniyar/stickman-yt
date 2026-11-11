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
        (ep / "scenes" / f"{i}.html").write_text(scene_html(i))


def scene_html(sid, comp_id=None, key=None):
    comp_id = comp_id or sid
    key = key or sid
    return (
        "<template>\n<style>#root{position:absolute;inset:0}</style>\n"
        f'<div id="root" data-composition-id="{comp_id}" data-width="1920" data-height="1080"></div>\n'
        f'<script>const tl = gsap.timeline({{ paused: true }}); window.__timelines["{key}"] = tl;</script>\n'
        "</template>\n"
    )

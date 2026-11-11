import json
import re
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib" / "stickman"
POSES = ["stand", "point", "think", "shrug", "celebrate", "sad", "walk", "run", "sit", "explain", "shocked", "hold-sign"]
JOINTS = ["head", "torso", "armL_upper", "armL_lower", "armR_upper", "armR_lower",
          "legL_upper", "legL_lower", "legR_upper", "legR_lower"]
PROPS = ["coin", "money-stack", "house", "car", "credit-card", "bank", "chart-up", "chart-down",
         "lightbulb", "atom", "chip", "phone", "clock", "question-mark", "arrow"]


def test_poses_json_complete():
    poses = json.loads((LIB / "poses.json").read_text())
    assert sorted(poses) == sorted(POSES)
    for name, p in poses.items():
        assert sorted(p) == sorted(JOINTS), name
        assert all(isinstance(v, (int, float)) for v in p.values()), name


def test_stickman_js_embeds_same_poses():
    js = (LIB / "stickman.js").read_text()
    m = re.search(r"/\*POSES\*/(.*?)/\*END POSES\*/", js, re.S)
    assert m, "stickman.js must embed poses between /*POSES*/ and /*END POSES*/"
    assert json.loads(m.group(1)) == json.loads((LIB / "poses.json").read_text())


def test_stickman_js_has_all_props_and_api():
    js = (LIB / "stickman.js").read_text()
    for prop in PROPS:
        assert f'"{prop}"' in js, prop
    for fn in ("mount", "pose", "breathe", "walk", "prop"):
        assert re.search(rf"\b{fn}\s*[:(]", js), fn
    assert "Math.random" not in js and "Date.now" not in js and "repeat: -1" not in js


def test_thumbnail_template_placeholders():
    html = (LIB / "thumbnail.html").read_text()
    assert "{{TEXT}}" in html and "{{POSE}}" in html
    assert 'data-width="1280"' in html and 'data-height="720"' in html

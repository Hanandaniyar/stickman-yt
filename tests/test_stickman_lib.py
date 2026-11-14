import json
import re

import pytest
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


BG_LIB = LIB.parent / "backgrounds"
BACKGROUNDS = ["street", "city-skyline", "store-checkout", "supermarket", "kitchen", "living-room", "office",
               "bank-hall", "car-dealership", "highway", "data-center", "factory", "park", "classroom",
               "paper-grid", "studio"]


def test_backgrounds_complete():
    names = sorted(p.stem for p in BG_LIB.glob("*.svg"))
    assert names == sorted(BACKGROUNDS)


@pytest.mark.parametrize("name", BACKGROUNDS)
def test_background_svg_contract(name):
    import xml.etree.ElementTree as ET

    text = (BG_LIB / f"{name}.svg").read_text()
    root = ET.fromstring(text)  # well-formed XML
    assert root.get("viewBox") == "0 0 1920 1080"
    assert root.get("width") == "1920" and root.get("height") == "1080"
    ids = {el.get("id") for el in root.iter()}
    assert {"far", "mid", "near"} <= ids, "layers for parallax"
    assert "<text" not in text, "no text/brand names in backgrounds"
    assert "http://" not in text.replace("http://www.w3.org/", "") and "https://" not in text, "no external refs"
    assert "<image" not in text, "drawn with vector shapes only"
    other = [i for i in ids if i and i not in ("far", "mid", "near", "base")]
    assert all(i.startswith(f"{name}-") for i in other), f"ids must be prefixed with '{name}-': {other}"


def test_stickman_js_has_scene_helpers():
    js = (LIB / "stickman.js").read_text()
    for fn in ("background", "registerBackgrounds", "camera", "parallax", "enter", "exit"):
        assert re.search(rf"\b{fn}\s*[:(]", js), fn
    assert "Math.random" not in js and "Date.now" not in js and "repeat: -1" not in js


NODE_HARNESS = r"""
const calls = [];
global.window = {};
global.gsap = { parseEase: () => (p) => p };
const fakeEl = (id) => ({ id, style: {}, innerHTML: "", _q: {},
  querySelector(sel) { const m = this.innerHTML.match(new RegExp('<(\\w+)[^>]*id="' + sel.slice(1) + '"'));
    if (sel === "svg") return { setAttribute() {}, style: {} };
    return m ? { id: sel.slice(1) } : null; } });
require(process.argv[1]);
const S = window.Stickman;
const tl = { fromTo: (el, a, b, at) => calls.push({ el: el.id, a, b, at }) };
S.registerBackgrounds({ demo: '<svg id="x"><defs><linearGradient id="demo-sky"/></defs><g id="far"/><g id="mid"/><g id="near"/><rect fill="url(#demo-sky)"/></svg>' });
const el = fakeEl("s04-bg");
const bg = S.background(el, "demo");
const cam = fakeEl("s04-cam");
S.camera(tl, cam, { from: { scale: 1 }, to: { scale: 1.2, focus: 1500 }, at: 0.5, duration: 3 });
S.camera(tl, cam, { preset: "pull-out", at: 3.5, duration: 1 });
S.parallax(tl, bg, { x: 100, at: 0, duration: 4 });
let unknown = null;
try { S.background(fakeEl("s05-bg"), "moon"); } catch (e) { unknown = e.message; }
console.log(JSON.stringify({ html: el.innerHTML, layers: [bg.far && bg.far.id, bg.mid && bg.mid.id, bg.near && bg.near.id],
  calls, unknown, names: S.backgrounds(), ground: S.GROUND }));
"""


def _run_node():
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node tidak tersedia")
    out = subprocess.run(["node", "-e", NODE_HARNESS, str(LIB / "stickman.js")], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_background_prefixes_ids_and_exposes_layers():
    r = _run_node()
    assert 'id="s04-bg-demo-sky"' in r["html"] and "url(#s04-bg-demo-sky)" in r["html"]
    assert r["layers"] == ["s04-bg-far", "s04-bg-mid", "s04-bg-near"]
    assert "moon" in r["unknown"] and r["names"] == ["demo"] and r["ground"] == 840


def test_camera_keeps_floor_line_and_never_shows_edges():
    r = _run_node()
    cams = [c for c in r["calls"] if c["el"] == "s04-cam"]
    first, second = cams
    b = first["b"]
    assert b["scale"] == 1.2 and first["at"] == 0.5 and b["duration"] == 3
    # floor at y=840 stays at 840: 540 + s*(840-540) + y == 840
    assert abs(540 + 1.2 * 300 + b["y"] - 840) < 1e-6
    assert abs(b["x"]) <= (1.2 - 1) * 960 + 1e-6  # clamped: background edge never visible
    assert b["immediateRender"] is True and second["b"]["immediateRender"] is False


def test_parallax_moves_far_less_than_near():
    r = _run_node()
    par = {c["el"]: c for c in r["calls"] if c["el"].startswith("s04-bg-")}
    span = {k: abs(v["a"]["x"] - v["b"]["x"]) for k, v in par.items()}
    assert span["s04-bg-far"] < span["s04-bg-mid"] < span["s04-bg-near"] == 100

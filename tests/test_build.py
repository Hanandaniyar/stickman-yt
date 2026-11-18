import json
import re

import pytest

from sty.build import build_composition, caption_groups
from sty.episode import create_episode
from tests.conftest import write_scenes


def _timing(ep, scenes, words=None):
    t = {"duration": scenes[-1][2], "scenes": [{"id": i, "start": s, "end": e} for i, s, e in scenes], "words": words or []}
    (ep / "timing.json").write_text(json.dumps(t))
    (ep / "audio").mkdir(exist_ok=True)
    (ep / "audio" / "narration.wav").write_bytes(b"RIFF")


@pytest.fixture
def ep(tmp_path):
    ep = create_episode("x", tmp_path)
    write_scenes(ep, ["s01", "s02"])
    _timing(ep, [("s01", 0.0, 1.0), ("s02", 1.25, 3.0)],
            [{"w": "Money", "start": 0.1, "end": 0.4}, {"w": "talks.", "start": 0.5, "end": 0.9},
             {"w": "Prices", "start": 1.3, "end": 1.7}, {"w": "<rise>", "start": 1.8, "end": 2.2}])
    return ep


def _host(html, sid):
    return re.search(rf'<div[^>]*id="{sid}"[^>]*>', html).group(0)


def test_scenes_placed_at_timing_start(ep):
    html = build_composition(ep).read_text()
    s2 = _host(html, "s02")
    assert 'data-start="1.25"' in s2 and 'data-composition-src="compositions/s02.html"' in s2
    assert 'data-duration="1.25"' in _host(html, "s01")  # slot runs until the next scene starts
    assert 'data-duration="2.75"' in s2  # last slot runs to the end (3.0 + 1.0 tail)
    assert 'data-duration="4.0"' in _host(html, "root")
    assert (ep / "build" / "compositions" / "s02.html").exists()
    assert (ep / "build" / "assets" / "stickman" / "stickman.js").exists()
    assert (ep / "build" / "assets" / "narration.wav").exists()
    assert 'id="narration"' in html


def test_music_optional(ep, tmp_path, monkeypatch):
    from sty import build as b

    monkeypatch.setattr(b, "_media_duration", lambda p: 120.0)
    html = build_composition(ep).read_text()
    assert 'id="music' not in html
    music = tmp_path / "assets" / "music"
    music.mkdir(parents=True)
    (music / "calm.mp3").write_bytes(b"ID3")
    data = json.loads((ep / "narration.json").read_text())
    data["music"] = "assets/music/calm.mp3"
    (ep / "narration.json").write_text(json.dumps(data))
    html = build_composition(ep).read_text()
    assert re.search(r'<audio[^>]*id="music-0"[^>]*data-volume="0.08"', html)
    assert (ep / "build" / "assets" / "music.mp3").exists()


def test_captions_escaped_and_grouped(ep):
    build_composition(ep)
    cap = (ep / "build" / "compositions" / "captions.html").read_text()
    assert "&lt;rise&gt;" in cap and "<rise>" not in cap
    assert 'data-composition-id="captions"' in cap and '__timelines["captions"]' in cap


def test_caption_groups_break_on_sentence_and_limit():
    words = [{"w": f"w{i}", "start": i * 0.3, "end": i * 0.3 + 0.25} for i in range(7)]
    words[1]["w"] = "end."
    groups = caption_groups(words, max_words=5)
    assert [len(g) for g in groups] == [2, 5]


def test_missing_timing_message(tmp_path):
    ep = create_episode("y", tmp_path)
    write_scenes(ep, ["s01"])
    with pytest.raises(FileNotFoundError, match="jalankan sty voice dulu"):
        build_composition(ep)


def test_fragment_scene_id_mismatch_rejected(ep):
    from tests.conftest import scene_html

    (ep / "scenes" / "s02.html").write_text(scene_html("s02", comp_id="s05"))
    with pytest.raises(ValueError, match="s02"):
        build_composition(ep)


def test_timing_scene_list_must_match_narration(ep):
    _timing(ep, [("s01", 0.0, 1.0)])
    with pytest.raises(ValueError, match="sty voice --force"):
        build_composition(ep)


def test_caption_groups_never_overlap(ep):
    words = [{"w": f"w{i}", "start": 0.3 * i, "end": 0.3 * i + 0.25} for i in range(12)]
    t = json.loads((ep / "timing.json").read_text())
    t["words"] = words
    (ep / "timing.json").write_text(json.dumps(t))
    build_composition(ep)
    cap = (ep / "build" / "compositions" / "captions.html").read_text()
    spans = [(float(s), float(d)) for s, d in re.findall(r'class="clip cap" data-start="([\d.]+)" data-duration="([\d.]+)"', cap)]
    for (s1, d1), (s2, _) in zip(spans, spans[1:]):
        assert s1 + d1 <= s2 + 1e-9


def test_music_loops_to_cover_video(ep, tmp_path, monkeypatch):
    from sty import build as b

    music = tmp_path / "assets" / "music"
    music.mkdir(parents=True)
    (music / "calm.mp3").write_bytes(b"ID3")
    data = json.loads((ep / "narration.json").read_text())
    data["music"] = "assets/music/calm.mp3"
    (ep / "narration.json").write_text(json.dumps(data))
    monkeypatch.setattr(b, "_media_duration", lambda p: 1.5)  # video total is 4.0 s
    html = build_composition(ep).read_text()
    clips = re.findall(r'<audio[^>]*id="music-(\d+)"[^>]*data-start="([\d.]+)"[^>]*data-duration="([\d.]+)"', html)
    assert [(int(i), float(s), float(d)) for i, s, d in clips] == [(0, 0.0, 1.5), (1, 1.5, 1.5), (2, 3.0, 1.0)]


def _set_scene(ep, idx, **fields):
    data = json.loads((ep / "narration.json").read_text())
    data["scenes"][idx].update(fields)
    (ep / "narration.json").write_text(json.dumps(data))


def test_sfx_placed_at_scene_offset(ep, monkeypatch):
    from sty import build as b

    monkeypatch.setattr(b, "_media_duration", lambda p: 0.5)
    _set_scene(ep, 1, sfx=[{"name": "coin", "at": 0.4}])
    html = build_composition(ep).read_text()
    tag = re.search(r'<audio[^>]*id="sfx-0"[^>]*>', html).group(0)
    assert 'src="assets/sfx/coin.mp3"' in tag
    assert 'data-start="1.65"' in tag and 'data-duration="0.5"' in tag
    assert 'data-volume="0.35"' in tag
    assert (ep / "build" / "assets" / "sfx" / "coin.mp3").exists()
    assert not (ep / "build" / "assets" / "sfx" / "boing.mp3").exists()  # only the sounds used are copied


def test_sfx_anchored_to_word_in_its_scene(ep, monkeypatch):
    from sty import build as b

    monkeypatch.setattr(b, "_media_duration", lambda p: 0.5)
    _set_scene(ep, 1, text="Prices rise.", sfx=[{"name": "boing", "word": "prices", "volume": 0.6}])
    html = build_composition(ep).read_text()
    tag = re.search(r'<audio[^>]*id="sfx-0"[^>]*>', html).group(0)
    assert 'data-start="1.3"' in tag and 'data-volume="0.6"' in tag


def test_sfx_clipped_to_video_end(ep, monkeypatch):
    from sty import build as b

    monkeypatch.setattr(b, "_media_duration", lambda p: 5.0)
    _set_scene(ep, 1, sfx=[{"name": "drumroll", "at": 2.0}])  # starts at 3.25, video ends at 4.0
    html = build_composition(ep).read_text()
    assert 'data-duration="0.75"' in re.search(r'<audio[^>]*id="sfx-0"[^>]*>', html).group(0)


def test_emoji_used_by_scenes_are_copied(ep):
    scene = (ep / "scenes" / "s01.html").read_text()
    (ep / "scenes" / "s01.html").write_text(scene.replace("></div>", '><img src="assets/emoji/automobile.svg"></div>', 1))
    build_composition(ep)
    assert (ep / "build" / "assets" / "emoji" / "automobile.svg").exists()
    assert not (ep / "build" / "assets" / "emoji" / "lemon.svg").exists()


def test_backgrounds_used_by_scenes_are_bundled(ep):
    scene = (ep / "scenes" / "s01.html").read_text()
    (ep / "scenes" / "s01.html").write_text(
        scene.replace("</script>", 'Stickman.background(document.getElementById("s01-bg"), "kitchen");</script>', 1))
    scene = (ep / "scenes" / "s02.html").read_text()
    (ep / "scenes" / "s02.html").write_text(scene.replace("></div>", '><img src="assets/backgrounds/park.svg"></div>', 1))
    html = build_composition(ep).read_text()
    bg = ep / "build" / "assets" / "backgrounds"
    assert (bg / "kitchen.svg").exists() and (bg / "park.svg").exists()
    assert not (bg / "office.svg").exists()  # only the backgrounds used are copied
    js = (bg / "backgrounds.js").read_text()
    assert '"kitchen"' in js and '"park"' in js and '"office"' not in js
    assert "Stickman.registerBackgrounds" in js
    head = html.split("</head>")[0]
    assert head.index("assets/stickman/stickman.js") < head.index("assets/backgrounds/backgrounds.js")


def test_backgrounds_script_present_even_when_unused(ep):
    html = build_composition(ep).read_text()
    assert "assets/backgrounds/backgrounds.js" in html
    assert (ep / "build" / "assets" / "backgrounds" / "backgrounds.js").exists()


def _make_short(ep):
    n = json.loads((ep / "narration.json").read_text())
    n["format"] = "short"
    (ep / "narration.json").write_text(json.dumps(n))


def test_short_format_is_vertical_1080x1920(ep):
    _make_short(ep)
    html = build_composition(ep).read_text()
    assert 'data-width="1080" data-height="1920"' in _host(html, "root")
    assert 'data-width="1080" data-height="1920"' in _host(html, "s01")
    assert 'data-width="1080" data-height="1920"' in _host(html, "captions")
    assert "width: 1080px; height: 1920px" in html
    assert "window.STICKMAN_FRAME = {w: 1080, h: 1920}" in html
    assert html.index("STICKMAN_FRAME") < html.index("stickman.js")
    caps = (ep / "build" / "compositions" / "captions.html").read_text()
    assert 'data-width="1080" data-height="1920"' in caps and "width: 1080px" in caps


def test_short_captions_use_short_groups(ep):
    _make_short(ep)
    build_composition(ep)
    caps = (ep / "build" / "compositions" / "captions.html").read_text()
    assert 'id="cap-0"' in caps and 'id="cap-0-2"' not in caps  # max 3 words per line, "Money talks." stays 2


def test_landscape_is_default(ep):
    html = build_composition(ep).read_text()
    assert 'data-width="1920" data-height="1080"' in _host(html, "root")
    assert "STICKMAN_FRAME = {w: 1920, h: 1080}" in html


def test_unknown_format_rejected(ep):
    n = json.loads((ep / "narration.json").read_text())
    n["format"] = "square"
    (ep / "narration.json").write_text(json.dumps(n))
    with pytest.raises(ValueError, match="format"):
        build_composition(ep)

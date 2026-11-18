import json
import pytest

from sty.episode import (
    approve, create_episode, episode_dir, load_status, record_review,
    request, revision_rounds, set_stage, validate_narration,
)
from tests.conftest import scene_html, write_scenes


def test_numbering(tmp_path):
    a = create_episode("a", tmp_path)
    b = create_episode("b", tmp_path)
    assert a.name.startswith("001-") and b.name.startswith("002-")


def test_slug_normalized(tmp_path):
    assert create_episode("Why Inflation?!", tmp_path).name == "001-why-inflation"


def test_new_episode_status(ep):
    st = load_status(ep)
    assert st["stage"] == "topics" and st["request"] is None
    assert (ep / "reviews").is_dir() and (ep / "scenes").is_dir()


def test_review_rounds(ep):
    assert record_review(ep, "script", "REVISI", "hook lambat") == 1
    assert record_review(ep, "script", "REVISI", "fakta salah") == 2
    assert (ep / "reviews" / "script-2.md").read_text().startswith("# script")
    assert revision_rounds(ep, "script") == 2
    assert revision_rounds(ep, "topics") == 0


def test_invalid_verdict(ep):
    with pytest.raises(ValueError):
        record_review(ep, "script", "OK", "x")


def test_invalid_stage(ep):
    with pytest.raises(ValueError):
        set_stage(ep, "publish")


def test_resume_reads_last_stage(ep):
    set_stage(ep, "scenes")
    assert load_status(ep)["stage"] == "scenes"


def test_episode_ref_lookup(ep, tmp_path):
    assert episode_dir("1", tmp_path) == ep
    assert episode_dir("001", tmp_path) == ep
    assert episode_dir(ep.name, tmp_path) == ep
    with pytest.raises(FileNotFoundError):
        episode_dir("7", tmp_path)


def test_validate_narration_ok(ep):
    write_scenes(ep, ["s01", "s02"])
    assert validate_narration(ep) == []


def test_request_render_requires_valid_narration(ep):
    write_scenes(ep, ["s01", "s02", "s03"])
    (ep / "scenes" / "s03.html").unlink()
    with pytest.raises(ValueError, match="s03"):
        request(ep, "render")
    assert load_status(ep)["request"] is None


def test_validate_catches_bad_ids_and_text(ep):
    write_scenes(ep, ["s01", "s01", "s03"])
    errs = "\n".join(validate_narration(ep))
    assert "duplikat" in errs and "urutan" in errs


def test_validate_scene_id_mismatch(ep):
    write_scenes(ep, ["s01"])
    (ep / "scenes" / "s01.html").write_text(scene_html("s01", comp_id="s09"))
    assert any("s01" in e and "data-composition-id" in e for e in validate_narration(ep))


def test_validate_timeline_key_mismatch(ep):
    write_scenes(ep, ["s01"])
    (ep / "scenes" / "s01.html").write_text(scene_html("s01", key="main"))
    assert any("s01" in e and "__timelines" in e for e in validate_narration(ep))


def test_validate_requires_template(ep):
    write_scenes(ep, ["s01"])
    (ep / "scenes" / "s01.html").write_text('<div id="root" data-composition-id="s01"></div>')
    assert any("s01" in e and "<template>" in e for e in validate_narration(ep))


def test_validate_missing_music(ep):
    write_scenes(ep, ["s01"], music="assets/music/nope.mp3")
    assert any("musik" in e for e in validate_narration(ep))


def test_request_render_ok(ep):
    write_scenes(ep, ["s01"])
    request(ep, "render")
    assert load_status(ep)["request"] == "render"


def test_request_upload_requires_final_approval(ep):
    with pytest.raises(PermissionError, match="butuh persetujuan akhir"):
        request(ep, "upload")


def test_approve_final_sets_stage(ep):
    approve(ep, "final")
    st = load_status(ep)
    assert st["approvals"]["final"] is True and st["stage"] == "approved"


def test_request_upload_requires_release(ep):
    approve(ep, "final")
    with pytest.raises(PermissionError, match="render"):
        request(ep, "upload")


def test_request_render_clears_final_approval(ep):
    write_scenes(ep, ["s01"])
    approve(ep, "final")
    request(ep, "render")
    assert load_status(ep)["approvals"]["final"] is False


def test_request_upload_refuses_when_already_uploaded(ep):
    from sty.episode import _update

    approve(ep, "final")
    _update(ep, release_url="https://gh/rel", youtube_id="abc123")
    with pytest.raises(PermissionError, match="sudah diunggah"):
        request(ep, "upload")


def _narr_with(ep, **fields):
    from tests.conftest import write_scenes

    write_scenes(ep, ["s01"])
    data = json.loads((ep / "narration.json").read_text())
    data["scenes"][0].update(fields)
    (ep / "narration.json").write_text(json.dumps(data))


def test_validate_sfx_unknown_name(ep):
    from sty.episode import validate_narration

    _narr_with(ep, sfx=[{"name": "kazoo-solo", "at": 0.1}])
    assert any("kazoo-solo" in e for e in validate_narration(ep))


def test_validate_sfx_needs_at_or_word_in_text(ep):
    from sty.episode import validate_narration

    _narr_with(ep, sfx=[{"name": "coin"}, {"name": "boing", "word": "banana"}, {"name": "boing", "word": "narration"}])
    errs = validate_narration(ep)
    assert len(errs) == 2 and any("banana" in e for e in errs)


def test_validate_unknown_emoji(ep):
    from sty.episode import validate_narration

    _narr_with(ep)
    (ep / "scenes" / "s01.html").write_text(
        (ep / "scenes" / "s01.html").read_text().replace("></div>", '><img src="assets/emoji/not-a-thing.svg"></div>', 1))
    assert any("not-a-thing" in e for e in validate_narration(ep))


def test_background_names_found_in_scene():
    from sty.episode import background_names

    html = ('<img src="assets/backgrounds/park.svg">\n'
            '<script>const bg = Stickman.background(document.getElementById("s01-bg"), "kitchen");\n'
            "Stickman.background($('bg'), 'bank-hall', { parallax: true });</script>")
    assert background_names(html) == {"park", "kitchen", "bank-hall"}


def test_validate_unknown_background(ep):
    from sty.episode import validate_narration

    _narr_with(ep)
    scene = (ep / "scenes" / "s01.html").read_text()
    (ep / "scenes" / "s01.html").write_text(
        scene.replace("</script>", 'Stickman.background(document.body, "moon-base");</script>', 1))
    errs = validate_narration(ep)
    assert any("moon-base" in e and "lib/backgrounds" in e for e in errs)


def test_validate_known_background_ok(ep):
    from sty.episode import validate_narration

    _narr_with(ep)
    scene = (ep / "scenes" / "s01.html").read_text()
    (ep / "scenes" / "s01.html").write_text(
        scene.replace("</script>", 'Stickman.background(document.body, "kitchen");</script>', 1))
    assert validate_narration(ep) == []


def test_sfx_path_prefers_lib_then_hyperframes_package(tmp_path, monkeypatch):
    from sty import episode as e
    lib, npm = tmp_path / "lib", tmp_path / "npm"
    lib.mkdir(); npm.mkdir()
    (lib / "coin.mp3").write_bytes(b"a")
    (npm / "whoosh.mp3").write_bytes(b"b")
    (npm / "coin.mp3").write_bytes(b"c")
    monkeypatch.setattr(e, "SFX_LIB", lib)
    monkeypatch.setattr(e, "SFX_NPM", npm)
    assert e.sfx_path("coin") == lib / "coin.mp3"
    assert e.sfx_path("whoosh") == npm / "whoosh.mp3"  # Pixabay files are not stored in the repo
    assert e.sfx_path("kazoo") is None


def test_pixabay_sfx_not_stored_in_repo():
    from sty.episode import SFX_LIB
    credits = (SFX_LIB / "CREDITS.md").read_text()
    for name in ("whoosh", "pop", "chime", "click", "sparkle", "riser"):
        assert not (SFX_LIB / f"{name}.mp3").exists(), name
        assert name in credits

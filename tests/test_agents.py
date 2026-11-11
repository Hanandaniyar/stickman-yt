from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
AGENTS = {
    "udin": {"WebSearch", "WebFetch", "Read", "Write", "Bash"},
    "udan": {"Read", "Write", "WebSearch", "WebFetch"},
    "udun": {"Read", "Write", "Edit", "Bash"},
    "udon": {"Read", "Write", "Bash"},
}


def _front(path):
    text = path.read_text()
    assert text.startswith("---\n"), path
    return yaml.safe_load(text.split("---\n")[1]), text


@pytest.mark.parametrize("name", AGENTS)
def test_agent_frontmatter(name):
    fm, body = _front(ROOT / ".claude" / "agents" / f"{name}.md")
    assert fm["name"] == name
    assert fm["description"].strip()
    assert {t.strip() for t in fm["tools"].split(",")} == AGENTS[name]
    assert "notify:" in body  # every agent closes with a notify line in its commit


def test_handur_mentions_gates():
    fm, text = _front(ROOT / ".claude" / "skills" / "handur" / "SKILL.md")
    assert fm["name"] == "handur"
    for needle in ("config.json", "max_revision_rounds", "sty review", "sty approve", "sty request",
                   "udin", "udan", "udun", "udon", "rubric.md"):
        assert needle in text, needle
    assert (ROOT / ".claude" / "skills" / "handur" / "rubric.md").exists()


def test_udon_upload_only_after_final_approval():
    text = (ROOT / ".claude" / "agents" / "udon.md").read_text()
    assert "hanya setelah persetujuan akhir" in text


def test_udun_uses_stickman_and_forbids_paid_features():
    text = (ROOT / ".claude" / "agents" / "udun.md").read_text()
    assert "lib/stickman/README.md" in text and "sty check" in text and "sty request" in text


def test_claude_md_forbidden_commands_listed():
    text = (ROOT / "CLAUDE.md").read_text()
    for bad in ("auth login", "cloud render", "media-use generate", "style-sampling", "feedback"):
        assert bad in text, bad


def test_claude_md_has_channel():
    text = (ROOT / "CLAUDE.md").read_text()
    assert "@Economicforadults" in text and "Handur" in text


def test_ipad_guide_exists():
    assert "Handur" in (ROOT / "docs" / "setup" / "ipad.md").read_text()

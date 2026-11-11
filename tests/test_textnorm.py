import pytest

from sty.textnorm import normalize_for_tts


@pytest.mark.parametrize("raw,expected", [
    ("$1,500", "one thousand five hundred dollars"),
    ("7%", "seven percent"),
    ("401(k)", "four oh one k"),
    ("in 2026", "in twenty twenty-six"),
    ("$3.5 trillion", "three point five trillion dollars"),
    ("AI & crypto", "AI and crypto"),
    ("$1 a day", "one dollar a day"),
    ("about 30 years", "about thirty years"),
])
def test_normalize(raw, expected):
    assert normalize_for_tts(raw) == expected

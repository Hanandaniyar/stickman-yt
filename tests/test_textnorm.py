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


@pytest.mark.parametrize("raw,expected", [
    ("In 2026, you save $1,500, then 7%.", "In twenty twenty-six, you save one thousand five hundred dollars, then seven percent."),
    ("$0.99", "ninety-nine cents"),
    ("$2.50", "two dollars and fifty cents"),
    ("$5k", "five thousand dollars"),
    ("$3B", "three billion dollars"),
    ("-3%", "minus three percent"),
    ("24/7", "twenty-four seven"),
])
def test_normalize_review_cases(raw, expected):
    assert normalize_for_tts(raw) == expected

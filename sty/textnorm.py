"""Ubah angka dan simbol menjadi kata supaya TTS membacanya dengan benar."""
import re

from num2words import num2words

_NUM = r"\d[\d,]*(?:\.\d+)?"
_SCALE = r"(?:\s+(thousand|million|billion|trillion))?"


def _words(num: str) -> str:
    value = num.replace(",", "")
    n = float(value) if "." in value else int(value)
    return num2words(n).replace(",", "").replace(" and ", " ")


def _money(m: re.Match) -> str:
    amount, scale = m.group(1), m.group(2)
    words = _words(amount)
    if scale:
        return f"{words} {scale} dollars"
    return f"{words} {'dollar' if amount == '1' else 'dollars'}"


def _number(m: re.Match) -> str:
    num = m.group(0)
    if re.fullmatch(r"1[1-9]\d\d|20\d\d", num):
        return num2words(int(num), to="year")
    return _words(num)


def normalize_for_tts(text: str) -> str:
    text = re.sub(r"\b401\(k\)", "four oh one k", text)
    text = text.replace("&", "and")
    text = re.sub(r"\$(" + _NUM + r")" + _SCALE, _money, text)
    text = re.sub(r"(" + _NUM + r")\s?%", lambda m: f"{_words(m.group(1))} percent", text)
    text = re.sub(r"(?<![\w.])" + _NUM + r"(?![\w])", _number, text)
    return re.sub(r"\s{2,}", " ", text).strip()

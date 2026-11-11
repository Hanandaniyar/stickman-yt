"""Ubah angka dan simbol menjadi kata supaya TTS membacanya dengan benar."""
import re

from num2words import num2words

_INT = r"\d{1,3}(?:,\d{3})+|\d+"
_NUM = rf"(?:{_INT})(?:\.\d+)?"
_SCALES = {"k": "thousand", "m": "million", "b": "billion", "t": "trillion",
           "thousand": "thousand", "million": "million", "billion": "billion", "trillion": "trillion"}
_SCALE = r"(?:\s*(k|K|M|B|T)\b|\s+(thousand|million|billion|trillion)\b)?"


def _words(num: str) -> str:
    value = num.replace(",", "")
    n = float(value) if "." in value else int(value)
    return num2words(n).replace(",", "").replace(" and ", " ")


def _money(m: re.Match) -> str:
    amount = m.group(1)
    scale = m.group(2) or m.group(3)
    if scale:
        return f"{_words(amount)} {_SCALES[scale.lower()]} dollars"
    value = amount.replace(",", "")
    if "." in value and len(value.split(".")[1]) == 2:
        dollars, cents = int(value.split(".")[0]), int(value.split(".")[1])
        cent_words = f"{num2words(cents)} {'cent' if cents == 1 else 'cents'}"
        if dollars == 0:
            return cent_words
        dollar_words = f"{_words(str(dollars))} {'dollar' if dollars == 1 else 'dollars'}"
        return dollar_words if cents == 0 else f"{dollar_words} and {cent_words}"
    return f"{_words(amount)} {'dollar' if value == '1' else 'dollars'}"


def _number(m: re.Match) -> str:
    num = m.group(0)
    if re.fullmatch(r"1[1-9]\d\d|20\d\d", num):
        return num2words(int(num), to="year")
    return _words(num)


def normalize_for_tts(text: str) -> str:
    text = re.sub(r"\b401\(k\)", "four oh one k", text)
    text = re.sub(r"\b24/7\b", "twenty-four seven", text)
    text = text.replace("&", "and")
    text = re.sub(rf"\$({_NUM}){_SCALE}", _money, text)
    text = re.sub(rf"(?<![\w.])-({_NUM})\s?%", lambda m: f"minus {_words(m.group(1))} percent", text)
    text = re.sub(rf"({_NUM})\s?%", lambda m: f"{_words(m.group(1))} percent", text)
    text = re.sub(rf"(?<![\w.]){_NUM}(?![\w])", _number, text)
    return re.sub(r"\s{2,}", " ", text).strip()

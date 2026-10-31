import glob, json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.pinyin_service import (
    numeric_to_tone_marks, tone_marks_to_numeric, split_pinyin, get_tone_number,
)
from services.srs_service import sm2_update

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.mark.parametrize("toned,numeric", [
    ("nǐ hǎo", "ni3 hao3"), ("zhōngguó", "zhong1guo2"), ("xièxie", "xie4xie5"),
    ("nǚ", "nü3"), ("lǜ", "lü4"), ("xiǎng", "xiang3"), ("diànhuà", "dian4hua4"),
    ("bù dàn", "bu4 dan4"), ("Chángchéng", "Chang2cheng2"), ("ér", "er2"), ("āyí", "a1yi2"),
    ("liǎng", "liang3"), ("xīngqī yī", "xing1qi1 yi1"),
])
def test_pinyin_known(toned, numeric):
    assert tone_marks_to_numeric(toned) == numeric
    assert numeric_to_tone_marks(numeric) == toned


def test_tone_helpers():
    assert split_pinyin("nǐ hǎo") == [("ni", 3), ("hao", 3)]
    assert get_tone_number("mā") == 1 and get_tone_number("ma") == 5


def _hsk_words():
    for f in sorted(glob.glob(str(DATA / "hsk" / "hsk[1-6].json"))):
        for w in json.load(open(f, encoding="utf-8")):
            yield f, w


def test_all_pinyin_roundtrips():
    """Every word's toned pinyin survives toned -> numeric -> toned (catches typos/bad marks)."""
    bad = []
    for f, w in _hsk_words():
        p = w["pinyin"]
        if numeric_to_tone_marks(tone_marks_to_numeric(p)) != p:
            bad.append((w["simplified"], p))
    assert not bad, bad


def test_handwritten_numeric_matches_toned():
    bad = [(w["simplified"], w["pinyin"], w["pinyin_numeric"]) for f, w in _hsk_words()
           if "pinyin_numeric" in w
           and tone_marks_to_numeric(w["pinyin"]) != w["pinyin_numeric"].replace("v", "ü")]  # lv4 == lü4
    assert not bad, bad


def test_word_data_shape():
    for f, w in _hsk_words():
        assert w["simplified"] and w["pinyin"] and w["definitions"], w
        assert len(w["simplified"]) <= 20 and len(w["pinyin"]) <= 100, w


def test_question_data_valid():
    for f in glob.glob(str(DATA / "tests" / "*.json")):
        for q in json.load(open(f, encoding="utf-8")):
            opts = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
            assert q["correct_option"] in "ABCD" and len(set(opts)) == 4, q["question_text"]


def _p(**kw):
    base = dict(ease_factor=2.5, interval_days=1, repetitions=0, is_learned=False,
                last_reviewed=None, next_review=None)
    return SimpleNamespace(**{**base, **kw})


def test_sm2_progression_and_reset():
    p = _p()
    sm2_update(p, 5); assert (p.repetitions, p.interval_days) == (1, 1)
    sm2_update(p, 5); assert (p.repetitions, p.interval_days) == (2, 6)
    sm2_update(p, 5); assert p.repetitions == 3 and p.interval_days == round(6 * 2.7)
    ef = p.ease_factor
    sm2_update(p, 1); assert (p.repetitions, p.interval_days) == (0, 1) and p.ease_factor < ef


def test_sm2_ease_floor_and_learned():
    p = _p()
    for _ in range(20):
        sm2_update(p, 3)
    assert p.ease_factor >= 1.3 and p.is_learned
    q = _p()
    for _ in range(10):
        sm2_update(q, 0)
    assert q.ease_factor == 1.3 and not q.is_learned

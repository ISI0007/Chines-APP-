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
    ("liǎng", "liang3"), ("nǚér", "nü3er2"), ("xīān", "xi1an1"), ("hǎoxiàng", "hao3xiang4"), ("wánr", "wan2r"), ("xīngqī yī", "xing1qi1 yi1"),
])
def test_pinyin_known(toned, numeric):
    assert tone_marks_to_numeric(toned) == numeric
    assert numeric_to_tone_marks(numeric) == toned


def test_apostrophe_is_dropped_one_way():
    assert tone_marks_to_numeric("xī'ān") == "xi1an1"  # numeric form has no apostrophe


def test_tone_helpers():
    assert split_pinyin("nǐ hǎo") == [("ni", 3), ("hao", 3)]
    assert get_tone_number("mā") == 1 and get_tone_number("ma") == 5


def _hsk_words():
    return json.load(open(DATA / "hsk" / "hsk30.json", encoding="utf-8"))


def test_hsk30_level_counts_match_official_syllabus():
    """Official HSK 3.0 new-words-per-level for levels 1-6 (after dropping 69 repeats + 16 example forms)."""
    from collections import Counter
    c = Counter(w["hsk_level"] for w in _hsk_words())
    assert c == {"HSK1": 510, "HSK2": 757, "HSK3": 958, "HSK4": 987, "HSK5": 1064, "HSK6": 1128}


def test_hsk30_unique_and_complete():
    words = _hsk_words()
    keys = [(w["simplified"], w["pinyin"]) for w in words]
    assert len(keys) == len(set(keys)), "duplicate (simplified, pinyin)"
    for w in words:
        assert w["definitions"] and all(isinstance(d, str) and d for d in w["definitions"]), w["simplified"]
        assert w["hsk_level"] in {f"HSK{n}" for n in range(1, 7)}
        assert len(w["simplified"]) <= 20 and len(w["traditional"]) <= 20 and len(w["pinyin"]) <= 100


def test_hsk30_no_noise_only_definitions():
    import re
    junk = re.compile(r"^(surname |name of |erhua variant of|variant of|old variant of|also pr\.|abbr\. for|see |\(Internet slang\))", re.I)
    bad = [w["simplified"] for w in _hsk_words() if all(junk.match(d) for d in w["definitions"])]
    assert not bad, bad


def test_hsk30_heteronyms_keep_their_own_meaning():
    by = {(w["simplified"], w["pinyin"]): w for w in _hsk_words()}
    assert by[("行", "xíng")]["hsk_level"] == "HSK1" and "walk" in " ".join(by[("行", "xíng")]["definitions"])
    assert by[("行", "háng")]["hsk_level"] == "HSK3" and "row" in " ".join(by[("行", "háng")]["definitions"])
    assert "long" in " ".join(by[("长", "cháng")]["definitions"])
    assert any(d in " ".join(by[("长", "zhǎng")]["definitions"]) for d in ("chief", "head", "grow"))
    assert by[("好", "hǎo")]["hsk_level"] == "HSK1" and by[("好", "hào")]["hsk_level"] == "HSK4"
    assert "also" in " ".join(by[("也", "yě")]["definitions"])  # was "surname Ye" before merging CEDICT entries


def test_all_pinyin_roundtrips():
    """Every word's toned pinyin survives toned -> numeric -> toned (catches bad marks / converter bugs)."""
    bad = []
    for w in _hsk_words():
        p = w["pinyin"].replace(" ", "")
        if numeric_to_tone_marks(tone_marks_to_numeric(p)) != p:
            bad.append((w["simplified"], w["pinyin"]))
    assert not bad, bad[:20]


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

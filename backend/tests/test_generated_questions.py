"""Independent verification of the generated HSK mock-test questions against hsk30.json."""
import glob, json, re
from collections import Counter
from pathlib import Path

import pytest

from services.pinyin_service import split_pinyin, tone_marks_to_numeric

DATA = Path(__file__).resolve().parent.parent / "data"
WORDS = {(w["simplified"], w["pinyin"]): w for w in json.load(open(DATA / "hsk" / "hsk30.json", encoding="utf-8"))}
FILES = sorted(glob.glob(str(DATA / "tests" / "hsk*_vocab.json")))
OPTS = ("option_a", "option_b", "option_c", "option_d")


def _qs():
    for f in FILES:
        level = Path(f).name.split("_")[0].upper()
        for q in json.load(open(f, encoding="utf-8")):
            yield level, q


def test_every_level_has_a_full_question_bank():
    per = Counter(level for level, _ in _qs())
    assert set(per) == {f"HSK{n}" for n in range(1, 7)} and all(n >= 180 for n in per.values()), per


def test_questions_are_well_formed_and_unique():
    seen = Counter()
    for level, q in _qs():
        opts = [q[k] for k in OPTS]
        assert len(set(opts)) == 4 and all(opts), q["question_text"]
        assert q["correct_option"] in "ABCD" and q["explanation"]
        seen[(level, q["question_text"])] += 1
    assert max(seen.values()) == 1


@pytest.mark.parametrize("level", [f"HSK{n}" for n in range(1, 7)])
def test_answers_match_the_official_data(level):
    checked = Counter()
    for lv, q in _qs():
        if lv != level:
            continue
        w = WORDS[(q["source_word"], q["source_pinyin"])]
        assert w["hsk_level"] == level
        opts = {k[-1].upper(): q[k] for k in OPTS}
        correct = opts[q["correct_option"]]
        foils = [v for L, v in opts.items() if L != q["correct_option"]]
        defs_text = " ; ".join(w["definitions"]).lower()
        if q["question_type"] == "pinyin":
            assert correct == w["pinyin"]
            n = len(split_pinyin(w["pinyin"]))
            for f in foils:
                assert f != w["pinyin"] and len(split_pinyin(f)) == n
            checked["pinyin"] += 1
        elif q["question_text"].startswith("What does"):
            assert q["question_text"] == f"What does {w['simplified']} ({w['pinyin']}) mean?"
            assert any(correct == d.split(";")[0].strip() for d in w["definitions"]), (w["simplified"], correct)
            for f in foils:  # a foil must not be (part of) a correct meaning
                assert not re.search(rf"\b{re.escape(f.lower())}\b", defs_text), (w["simplified"], f)
            checked["meaning"] += 1
        else:
            m = re.match(r'Which word means "(.+)"\?', q["question_text"])
            assert m and any(m.group(1) == d.split(";")[0].strip() for d in w["definitions"])
            assert correct == f"{w['simplified']} ({w['pinyin']})"
            for f in foils:
                other_word, other_py = re.match(r"(.+) \((.+)\)$", f).groups()
                other = WORDS[(other_word, other_py)]  # foil must be a real word of the dataset
                assert m.group(1).lower() not in [d.split(";")[0].strip().lower() for d in other["definitions"]], (m.group(1), f)
            checked["reverse"] += 1
    assert all(checked[k] >= 30 for k in ("pinyin", "meaning", "reverse")), checked

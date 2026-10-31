"""The committed writing-character curriculum must be well-formed and match the syllabus levels."""
import json
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CHARS = json.load(open(DATA / "writing" / "characters.json", encoding="utf-8"))


def test_characters_are_single_hanzi_with_pinyin_and_meaning():
    seen = set()
    for c in CHARS:
        assert len(c["char"]) == 1 and "一" <= c["char"] <= "鿿", c
        assert c["char"] not in seen
        seen.add(c["char"])
        assert c["pinyin"] and c["meaning"] and all(isinstance(m, str) and m for m in c["meaning"])
        assert c["hsk_level"] in {f"HSK{n}" for n in range(1, 7)}


def test_level_distribution_matches_official_writing_outline():
    # Official 书写字: ~100 for HSK1~2 combined, 150 each for HSK3-6 (a few lost to dedup repeats).
    c = Counter(x["hsk_level"] for x in CHARS)
    assert c["HSK1"] + c["HSK2"] >= 95          # the combined beginner band
    for lv in ("HSK3", "HSK4", "HSK5", "HSK6"):
        assert c[lv] >= 145, (lv, c[lv])
    assert 680 <= len(CHARS) <= 700


def test_characters_are_a_subset_of_the_vocabulary_hanzi():
    vocab_chars = {ch for w in json.load(open(DATA / "hsk" / "hsk30.json", encoding="utf-8")) for ch in w["simplified"]}
    missing = [c["char"] for c in CHARS if c["char"] not in vocab_chars]
    assert not missing, missing[:10]   # every writing char should appear in some HSK word

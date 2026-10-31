"""The committed audio MANIFEST must be consistent with the word list and the selection rules."""
import json
from collections import Counter
from pathlib import Path

import pytest

from services.pinyin_service import split_pinyin, tone_marks_to_numeric

DATA = Path(__file__).resolve().parent.parent / "data"
MANIFEST = DATA / "audio" / "MANIFEST.json"
pytestmark = pytest.mark.skipif(not MANIFEST.exists(), reason="run scripts/fetch_audio.py to generate the manifest")
WORDS = {(w["simplified"], w["pinyin"]): w for w in json.load(open(DATA / "hsk" / "hsk30.json", encoding="utf-8"))}
READINGS = Counter(h for h, _ in WORDS)


def _m():
    return json.load(open(MANIFEST, encoding="utf-8"))


def test_entries_exist_in_word_list_and_names_follow_the_rules():
    m = _m()
    assert m["with_audio"] == len(m["files"]) and m["total_entries"] == len(WORDS)
    names = set()
    for f in m["files"]:
        w = WORDS[(f["hanzi"], f["pinyin"])]
        assert w["hsk_level"] == f["level"] and f["file"] not in names
        names.add(f["file"])
        numeric = tone_marks_to_numeric(f["pinyin"]).replace(" ", "")
        if f["kind"] == "word":
            # never attach one recording to a hanzi that has several readings
            assert READINGS[f["hanzi"]] == 1 and f["file"] == f"{f['level'].lower()}/{f['hanzi']}.mp3"
        else:
            assert f["kind"] == "syllable" and len(split_pinyin(f["pinyin"])) == 1 and numeric[-1] in "1234"
            assert f["file"] == f"{f['level'].lower()}/{f['hanzi']}_{numeric}.mp3" and f["verified"] == "label"


def test_rejected_recordings_are_not_used_and_coverage_is_consistent():
    m = _m()
    used_words = {(f["hanzi"], f["pinyin"]) for f in m["files"] if f["kind"] == "word"}
    assert not [r for r in m["rejected_tone_mismatch"] if (r["hanzi"], r["pinyin"]) in used_words]
    for lv, c in m["coverage"].items():
        n = sum(1 for f in m["files"] if f["level"] == lv)
        assert c["word"] + c["syllable"] == n and c["pct"] == round(100 * n / c["total"], 1)
    assert m["with_audio"] / m["total_entries"] > 0.75


def test_local_files_match_manifest_when_present():
    root = DATA / "audio"
    if not any(root.glob("hsk1/*.mp3")):
        pytest.skip("audio files not downloaded on this machine")
    missing = [f["file"] for f in _m()["files"] if not (root / f["file"]).is_file() or (root / f["file"]).stat().st_size < 1000]
    assert not missing, missing[:10]

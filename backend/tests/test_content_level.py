"""Graded reading texts and grammar examples must use only words at or below their level."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import check_level as cl  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
LEVELS = cl.load_levels()


def _reading():
    for f in sorted((DATA / "reading").glob("hsk*_texts.json")):
        for t in json.load(open(f, encoding="utf-8")):
            yield t["hsk_level"], t["title"], t["content"]


def _grammar():
    for f in sorted((DATA / "grammar").glob("hsk*_grammar.json")):
        for l in json.load(open(f, encoding="utf-8")):
            for e in l["examples"]:
                yield l["hsk_level"], l["title"], e["zh"]


@pytest.mark.parametrize("kind,items", [("reading", list(_reading())), ("grammar", list(_grammar()))])
def test_content_stays_within_its_level(kind, items):
    assert items, f"no {kind} content found"
    offenders = []
    for level, title, text in items:
        bad = cl.check(text, int(level[3:]), LEVELS)
        if bad:
            offenders.append((level, title, text, [b["token"] for b in bad]))
    assert not offenders, offenders


def test_reading_and_grammar_present_for_hsk1_3():
    from collections import Counter
    rc = Counter(lv for lv, *_ in _reading())
    gc = Counter(lv for lv, t in {(lv, t) for lv, t, _ in _grammar()})
    for lv in ("HSK1", "HSK2", "HSK3"):
        assert rc[lv] == 6, (lv, rc[lv])
        assert gc[lv] == 8, (lv, gc[lv])

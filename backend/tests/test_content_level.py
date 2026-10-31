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


def test_hsk1_reading_and_grammar_are_present():
    assert sum(1 for lv, *_ in _reading() if lv == "HSK1") == 6
    assert len({t for lv, t, _ in _grammar() if lv == "HSK1"}) == 8

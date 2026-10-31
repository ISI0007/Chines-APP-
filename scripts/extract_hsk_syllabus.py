"""
Extract the vocabulary table from the official HSK syllabus PDF
(中外语言交流合作中心 / CTI "HSK 考试大纲", published 2025-11, in force from 2026-07).

Rows are reconstructed from cell POSITIONS (not line order) and the 48 pt rotated watermark is
dropped by font size/direction, so real words such as 国际 are not mistaken for watermark text.
Every row carries the syllabus sequence number, which lets us PROVE completeness:
  * sequence numbers must run 1..N with no gaps or duplicates
  * new words per level must match the syllabus totals

    pip install pymupdf
    python scripts/extract_hsk_syllabus.py --pdf "<path>/New HSK Syllabus - Vocabulary, Characters, Grammar.pdf" --out /tmp/syllabus_vocab.json
"""
import argparse
import json
import re
import sys
from collections import Counter

import pymupdf

FIRST_VOCAB_PAGE, LAST_VOCAB_PAGE = 3, 277          # 0-based PDF page indexes (printed pages 2-276)
# New words per level in the syllabus (cumulative 300/500/1000/2000/3600/5400, then 5600 for 7-9)
EXPECTED = {"1": 300, "2": 200, "3": 500, "4": 1000, "5": 1600, "6": 1800, "7-9": 5600}


def column(x: float) -> str:
    return "seq" if x < 130 else "level" if x < 200 else "word" if x < 310 else "pinyin" if x < 430 else "pos"


def page_rows(page):
    spans = []
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            if abs(line["dir"][1]) > 0.01:                 # rotated => watermark
                continue
            for s in line["spans"]:
                t = s["text"].strip()
                if t and s["size"] < 20:                   # 48 pt => watermark
                    spans.append((s["bbox"][0], (s["bbox"][1] + s["bbox"][3]) / 2, t))
    hdr = [y for _, y, t in spans if t == "序号"]
    if not hdr:
        return []
    spans = [s for s in spans if hdr[0] + 8 < s[1] < 790]  # below header, above the page-number footer
    seq = sorted((y, int(t)) for x, y, t in spans if column(x) == "seq" and t.isdigit())
    rows = []
    for i, (y, n) in enumerate(seq):
        lo, hi = y - 8, (seq[i + 1][0] - 8 if i + 1 < len(seq) else 790)
        cells = {"level": [], "word": [], "pinyin": [], "pos": []}
        for x, yy, t in sorted((s for s in spans if lo <= s[1] < hi), key=lambda s: (round(s[1]), s[0])):
            c = column(x)
            if c in cells:
                cells[c].append(t)
        rows.append({"seq": n, "level": "".join(cells["level"]), "word": "".join(cells["word"]),
                     "pinyin": " ".join(cells["pinyin"]), "pos": "".join(cells["pos"])})
    return rows


# The syllabus numbers words consecutively level by level, so the row number alone fixes the level.
SEQ_RANGES = [(300, "1"), (500, "2"), (1000, "3"), (2000, "4"), (3600, "5"), (5400, "6"), (11000, "7-9")]


def level_from_seq(n: int) -> str:
    return next(lv for top, lv in SEQ_RANGES if n <= top)


def primary_level(level: str) -> str:
    m = re.match(r"\d+", level)
    return "7-9" if m and m.group(0) == "7" else (m.group(0) if m else "?")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    doc = pymupdf.open(args.pdf)
    rows = [r for i in range(FIRST_VOCAB_PAGE, LAST_VOCAB_PAGE + 1) for r in page_rows(doc[i])]

    repaired = []
    for r in rows:  # a level cell can be lost by the PDF layout; the sequence range is authoritative
        if not re.match(r"\d", r["level"]):
            r["level"] = level_from_seq(r["seq"]); repaired.append(r["seq"])
    conflicts = [r for r in rows if primary_level(r["level"]) != level_from_seq(r["seq"])]
    seqs = [r["seq"] for r in rows]
    missing = sorted(set(range(1, max(seqs) + 1)) - set(seqs))
    dupes = [n for n, c in Counter(seqs).items() if c > 1]
    bad = [r for r in rows if not r["word"] or not r["pinyin"]]
    counts = Counter(primary_level(r["level"]) for r in rows)
    print(f"rows: {len(rows)}  max seq: {max(seqs)}  missing seq: {len(missing)}  duplicate seq: {len(dupes)}  malformed: {len(bad)}  level repaired from seq: {repaired}  level/seq conflicts: {len(conflicts)}")
    print("new words per level:", {k: counts[k] for k in EXPECTED})
    ok = all(counts[k] == v for k, v in EXPECTED.items()) and not missing and not dupes and not bad and not conflicts
    print("VALIDATION:", "PASS (matches the syllabus totals)" if ok else "FAIL")
    for r in bad[:10]:
        print("  malformed:", r)
    if missing:
        print("  missing seq sample:", missing[:20])
    json.dump(rows, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

"""
Extract the official WRITING-character outline (书写字) from the HSK syllabus PDF, levels 1-6.

The syllabus distinguishes 认读字 (characters to recognize) from 书写字 (characters to write). The
书写字 list is the authoritative set a learner must be able to hand-write, which is exactly the
curriculum for a stroke-order / writing module. Levels 7-9 are excluded.

Entries are numbered "N. 字" per level section; this reads them in order and tags each with its
level, dropping the rotated watermark.

    python scripts/extract_writing_chars.py --pdf "<...>/New HSK Syllabus ....pdf" --out /tmp/writing_chars.json
"""
import argparse
import json
import re
import sys

import pymupdf

# character -> lowest HSK level it appears at (from the built word list), to split the combined
# HSK1~2 writing page into per-level buckets.
def char_levels(hsk_json):
    import json as _j
    lv = {}
    for w in _j.load(open(hsk_json, encoding="utf-8")):
        n = int(w["hsk_level"][3:])
        for c in w["simplified"]:
            lv[c] = min(lv.get(c, 9), n)
    return lv

PAGES = range(300, 305)   # 0-based PDF pages: 书写字 for HSK1~2, 3, 4, 5, 6
HEADER = re.compile(r"HSK（(.+?)级）书写字")
LEVELMAP = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}


def header_levels(title: str):
    # "一）~（二" -> [1, 2]; "三" -> [3]
    return [LEVELMAP[c] for c in title if c in LEVELMAP]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--hsk", default="backend/data/hsk/hsk30.json")
    args = ap.parse_args()
    doc = pymupdf.open(args.pdf)
    clv = char_levels(args.hsk)

    rows, cur_levels, order = [], None, 0
    for i in PAGES:
        nums, chars, header_txt = [], [], ""
        for blk in doc[i].get_text("dict")["blocks"]:
            for line in blk.get("lines", []):
                if abs(line["dir"][1]) > 0.01:
                    continue
                for sp in line["spans"]:
                    t = sp["text"].strip()
                    if not t or "汉考" in t or t in ("际", "汉", "考", "国", "国际"):
                        continue
                    x0, y0, x1, y1 = sp["bbox"]
                    yc = (y0 + y1) / 2
                    header_txt += t
                    if re.fullmatch(r"\d+\s*[.．、]", t):
                        nums.append((int(re.match(r"\d+", t).group()), x1, yc))
                    elif re.fullmatch(r"[\u4e00-\u9fff]", t):
                        chars.append((x0, yc, t))
        m = HEADER.search(header_txt)
        levels = header_levels(m.group(1)) if m else cur_levels
        cur_levels = levels
        combined = len(levels) > 1
        # Pair each number with the nearest character to its right on the same line (layout-independent).
        for n, nx, ny in sorted(nums):
            cand = [(cx, c) for cx, cy, c in chars if abs(cy - ny) < 8 and cx > nx]
            if not cand:
                continue
            ch = min(cand)[1]
            order += 1
            if combined:
                lv = clv.get(ch, levels[0])
                lv = lv if lv in levels else levels[0]
            else:
                lv = levels[0]
            rows.append({"char": ch, "hsk_level": f"HSK{lv}", "order": order})

    seen, final = set(), []
    for r in rows:
        if r["char"] in seen:
            continue
        seen.add(r["char"])
        final.append(r)

    from collections import Counter
    per = Counter(r["hsk_level"] for r in final)
    print(f"writing chars (levels 1-6, deduped): {len(final)}")
    print("per level:", {k: per[k] for k in sorted(per, key=lambda x: x or 'z')})
    bad = [r for r in final if not r["hsk_level"] or len(r["char"]) != 1]
    print("malformed:", len(bad))
    json.dump(final, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

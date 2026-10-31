"""
Verify that a Chinese text uses only words at or below a target HSK level.

Segmentation is greedy longest-match against the allowed vocabulary itself (not a generic
tokenizer), so "下午" is one allowed word rather than 下 + 午. Anything that is not an allowed
word, an allowed single character, a whitelisted proper noun, a digit or punctuation is reported.

Used by build_reading.py / build_grammar.py and by the tests, so graded content can't silently
drift above its level.

    python scripts/check_level.py --level HSK1 --file some_text.txt
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT
HSK = BACKEND / "data" / "hsk" / "hsk30.json"

PUNCT = set("，。！？、：；“”‘’（）《》…—·. \n\t\r0123456789" + "".join(chr(c) for c in range(0x30, 0x3a)))
# Proper nouns are outside the graded vocabulary. HSK1 officially teaches the 小— prefix for names
# (小王, 小李), so a handful of common surnames are allowed as name components.
SURNAMES = set("王李张刘陈杨黄周吴马")
FUNCTION = {"没"}   # 没(有): HSK1 negative adverb that also appears bare before a verb
NAME_WHITELIST = {"小" + s for s in SURNAMES} | {"大" + s for s in SURNAMES} | {"老" + s for s in SURNAMES} | SURNAMES


def load_levels():
    lv = {}
    for w in json.loads(HSK.read_text(encoding="utf-8")):
        lv.setdefault(w["simplified"], int(w["hsk_level"][3:]))  # lowest level a word appears at
    return lv


def allowed_sets(levels: dict, target: int):
    words = {w for w, l in levels.items() if l <= target}
    return words, set("小大老") | SURNAMES    # only name components may appear outside a word


def segment(text: str, words: set):
    """Greedy longest-match (max word length 4). Yields (token, is_word)."""
    i, n = 0, len(text)
    toks = []
    while i < n:
        if text[i] in PUNCT:
            i += 1
            continue
        for L in range(min(4, n - i), 0, -1):
            if text[i:i + L] in words:
                toks.append((text[i:i + L], True))
                i += L
                break
        else:
            toks.append((text[i], False))
            i += 1
    return toks


def check(text: str, target: int, levels: dict):
    words, namechars = allowed_sets(levels, target)
    bad = []
    for tok, is_word in segment(text, words):
        if is_word or tok in NAME_WHITELIST or tok in namechars or tok in FUNCTION:
            continue
        # a single char that is itself a known HSK word (any level) is reported with its level
        bad.append({"token": tok, "level": levels.get(tok)})
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True)          # HSK1 .. HSK6
    ap.add_argument("--file", required=True)
    args = ap.parse_args()
    target = int(args.level.replace("HSK", ""))
    levels = load_levels()
    bad = check(Path(args.file).read_text(encoding="utf-8"), target, levels)
    if bad:
        print(f"FAIL: {len(bad)} out-of-level tokens:")
        for b in bad:
            where = f"HSK{b['level']}" if b["level"] else "not in any HSK list"
            print(f"  {b['token']}  ({where})")
        sys.exit(1)
    print(f"PASS: all tokens are {args.level} or below.")


if __name__ == "__main__":
    main()

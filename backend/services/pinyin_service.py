"""
Pinyin utilities: tone marks <-> numeric, syllable splitting, tone colours.

Handles run-together syllables ("zhōngguó" <-> "zhong1guo2") via a syllable regex,
not whitespace splitting.
"""
import re
from typing import List, Tuple

# toned vowel -> (plain vowel, tone)
_MARKED = {
    'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
    'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
    'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
    'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
    'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4),
    'ǖ': ('ü', 1), 'ǘ': ('ü', 2), 'ǚ': ('ü', 3), 'ǜ': ('ü', 4),
}
_TO_MARKED = {(v, t): ch for ch, (v, t) in _MARKED.items()}

TONE_COLORS = {1: "#E53935", 2: "#FF9800", 3: "#4CAF50", 4: "#2196F3", 5: "#9E9E9E"}

_VOWELS = "aeiouü" + "".join(_MARKED)
# one syllable: optional initial, vowel run, optional n/ng/r not followed by a vowel
_SYL = re.compile(
    rf"(?:zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?[{_VOWELS}]+(?:ng|n|r)?(?![{_VOWELS}])",
    re.IGNORECASE,
)
_NUMERIC_SYL = re.compile(r"([A-Za-zü:v]+?)([1-5])")


def _syllable_tone(syl: str) -> Tuple[str, int]:
    """Return (plain syllable, tone 1-5) for one toned syllable."""
    plain, tone = [], 5
    for ch in syl:
        if ch.lower() in _MARKED:
            base, tone = _MARKED[ch.lower()]
            plain.append(base.upper() if ch.isupper() else base)
        else:
            plain.append(ch)
    return "".join(plain), tone


def tone_marks_to_numeric(pinyin: str) -> str:
    """'nǐ hǎo' -> 'ni3 hao3'; 'zhōngguó' -> 'zhong1guo2'; neutral tone -> 5."""
    pinyin = pinyin.replace("'", "")

    def repl(m: re.Match) -> str:
        plain, tone = _syllable_tone(m.group(0))
        return f"{plain}{tone}"

    return _SYL.sub(repl, pinyin)


def _place_mark(plain: str, tone: int) -> str:
    """Put the tone mark on the right vowel (a/e first, 'ou' -> o, else last vowel)."""
    s = plain.replace("v", "ü").replace("u:", "ü")
    if tone == 5:
        return s
    low = s.lower()
    idx = None
    for v in "ae":
        if v in low:
            idx = low.index(v)
            break
    if idx is None and "ou" in low:
        idx = low.index("ou")
    if idx is None:
        for i in range(len(low) - 1, -1, -1):
            if low[i] in "iouü":
                idx = i
                break
    if idx is None:
        return s
    ch = s[idx]
    marked = _TO_MARKED.get((ch.lower(), tone))
    if not marked:
        return s
    return s[:idx] + (marked.upper() if ch.isupper() else marked) + s[idx + 1:]


def numeric_to_tone_marks(numeric: str) -> str:
    """'ni3 hao3' -> 'nǐ hǎo'; 'zhong1guo2' -> 'zhōngguó'."""
    return _NUMERIC_SYL.sub(lambda m: _place_mark(m.group(1), int(m.group(2))), numeric)


def split_pinyin(pinyin: str) -> List[Tuple[str, int]]:
    """Toned pinyin -> [(plain_syllable, tone), ...] (handles joined syllables)."""
    return [_syllable_tone(m.group(0)) for m in _SYL.finditer(pinyin.replace("'", ""))]


def get_tone_number(syllable: str) -> int:
    parts = split_pinyin(syllable)
    return parts[0][1] if parts else 5


def pinyin_to_html(pinyin: str) -> str:
    """Wrap each syllable in a tone-coloured span; other characters pass through."""
    def repl(m: re.Match) -> str:
        _, tone = _syllable_tone(m.group(0))
        return f'<span style="color:{TONE_COLORS[tone]}">{m.group(0)}</span>'
    return _SYL.sub(repl, pinyin)

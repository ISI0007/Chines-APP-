"""
Pinyin utilities: tone marks ↔ numeric, syllable parsing, comparison.
No external deps — pure Python lookup tables.
"""
from typing import List, Tuple

# Tone mark → numeric mapping
_TONE_MAP = {
    'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
    'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
    'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
    'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
    'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4),
    'ǖ': ('ü', 1), 'ǘ': ('ü', 2), 'ǚ': ('ü', 3), 'ǜ': ('ü', 4),
    'ü': ('ü', 5),
}

# Numeric → tone mark mapping
_NUMERIC_MAP = {
    ('a', 1): 'ā', ('a', 2): 'á', ('a', 3): 'ǎ', ('a', 4): 'à',
    ('e', 1): 'ē', ('e', 2): 'é', ('e', 3): 'ě', ('e', 4): 'è',
    ('i', 1): 'ī', ('i', 2): 'í', ('i', 3): 'ǐ', ('i', 4): 'ì',
    ('o', 1): 'ō', ('o', 2): 'ó', ('o', 3): 'ǒ', ('o', 4): 'ò',
    ('u', 1): 'ū', ('u', 2): 'ú', ('u', 3): 'ǔ', ('u', 4): 'ù',
    ('ü', 1): 'ǖ', ('ü', 2): 'ǘ', ('ü', 3): 'ǚ', ('ü', 4): 'ǜ',
}

TONE_COLORS = {
    1: "#E53935",  # Red   — flat
    2: "#FF9800",  # Orange — rising
    3: "#4CAF50",  # Green  — dipping
    4: "#2196F3",  # Blue   — falling
    5: "#9E9E9E",  # Grey   — neutral
}


def tone_marks_to_numeric(pinyin: str) -> str:
    """Convert toned pinyin to numeric: 'nǐ hǎo' → 'ni3 hao3'"""
    result = []
    i = 0
    while i < len(pinyin):
        ch = pinyin[i]
        if ch in _TONE_MAP:
            base, tone = _TONE_MAP[ch]
            # Insert the base letter first, then the tone number after the syllable
            result.append(base)
            # Look ahead for end of syllable to insert number
            j = i + 1
            while j < len(pinyin) and pinyin[j] not in (' ', '\t') and pinyin[j] not in _TONE_MAP:
                if pinyin[j] in 'aeiouüāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ':
                    break
                result.append(pinyin[j])
                j += 1
            result.append(str(tone))
            i = j
        else:
            result.append(ch)
            i += 1
    return ''.join(result)


def numeric_to_tone_marks(numeric: str) -> str:
    """Convert numeric pinyin to toned: 'ni3 hao3' → 'nǐ hǎo'"""
    syllables = numeric.split()
    result = []
    for syl in syllables:
        if not syl:
            continue
        # Extract trailing tone number
        if syl[-1].isdigit():
            tone = int(syl[-1])
            syl_base = syl[:-1]
        else:
            tone = 5
            syl_base = syl
        # Find the vowel to replace
        converted = _apply_tone(syl_base, tone)
        result.append(converted)
    return ' '.join(result)


def _apply_tone(syllable: str, tone: int) -> str:
    """Apply tone number to a syllable string."""
    # Tone placement rules (simplified):
    # 1. If there is an 'a' or 'e', it takes the tone mark
    # 2. If there is 'ou', 'o' takes the mark
    # 3. Otherwise the last vowel takes the mark
    vowels = 'aeiouü'
    s = syllable.lower()

    def replace_vowel(s: str, v: str, tone: int) -> str:
        key = (v, tone)
        if key in _NUMERIC_MAP:
            return s.replace(v, _NUMERIC_MAP[key], 1)
        return s

    if 'a' in s:
        return replace_vowel(syllable, 'a', tone)
    if 'e' in s:
        return replace_vowel(syllable, 'e', tone)
    if 'ou' in s:
        return replace_vowel(syllable, 'o', tone)
    # Last vowel
    for ch in reversed(syllable):
        if ch in vowels:
            return replace_vowel(syllable, ch, tone)
    return syllable


def get_tone_number(pinyin_syllable: str) -> int:
    """Extract tone number from a single syllable (toned or numeric)."""
    if pinyin_syllable and pinyin_syllable[-1].isdigit():
        return int(pinyin_syllable[-1])
    for ch in pinyin_syllable:
        if ch in _TONE_MAP:
            return _TONE_MAP[ch][1]
    return 5


def split_pinyin(pinyin: str) -> List[Tuple[str, int]]:
    """Split pinyin string into list of (syllable_no_tone, tone_number)."""
    result = []
    for syl in pinyin.split():
        tone = get_tone_number(syl)
        # Strip tone mark or digit
        clean = ''.join(
            _TONE_MAP[c][0] if c in _TONE_MAP else c
            for c in syl
            if not (c.isdigit())
        )
        result.append((clean, tone))
    return result


def pinyin_to_html(pinyin: str) -> str:
    """Wrap each syllable in a colored span based on tone."""
    parts = []
    for syl in pinyin.split():
        tone = get_tone_number(syl)
        color = TONE_COLORS.get(tone, "#333")
        parts.append(f'<span style="color:{color}">{syl}</span>')
    return ' '.join(parts)

#!/usr/bin/env python3
"""
build_course_manifest.py — scan hsk_course_assets/audio_extracted/ and generate
backend/data/hsk_course_assets/course_manifest.json.

Run from the project root:
    python scripts/build_course_manifest.py

The script:
  1. Walks audio_extracted/ looking for {lesson}-{section}.mp3 files
     (also handles the double-dash quirk: 2--1.mp3, 2--6.mp3)
  2. Builds a lesson-level manifest with 8 audio track slots per lesson
  3. Attaches known HSK-4A/4B lesson titles and answer-key PDF references
  4. Writes course_manifest.json (tracked in git — audio files are NOT)

Audio naming convention (HSK Standard Course 标准教程):
  {lesson_number}-{section_number}.mp3   (1-indexed, 8 sections per lesson)

Section map:
  1 → new_words      生词
  2 → text_1         课文一
  3 → extension      扩展词语
  4 → text_2         课文二
  5 → listening_1    综合练习（一）
  6 → listening_2    综合练习（二）
  7 → listening_3    综合练习（三）
  8 → hsk_practice   HSK综合练习
"""
import json
import re
import sys
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "backend" / "data" / "hsk_course_assets"
AUDIO_DIR  = ASSETS_DIR / "audio_extracted"
OUT_FILE   = ASSETS_DIR / "course_manifest.json"

# ── section mapping ───────────────────────────────────────────────────────────
SECTION_MAP = {
    1: ("new_words",    "生词",        "New Words"),
    2: ("text_1",       "课文一",      "Text 1"),
    3: ("extension",    "扩展词语",    "Extended Vocabulary"),
    4: ("text_2",       "课文二",      "Text 2"),
    5: ("listening_1",  "综合练习（一）", "Listening Exercise 1"),
    6: ("listening_2",  "综合练习（二）", "Listening Exercise 2"),
    7: ("listening_3",  "综合练习（三）", "Listening Exercise 3"),
    8: ("hsk_practice", "HSK综合练习", "HSK Mock Practice"),
}

# ── known lesson titles (HSK Standard Course 标准教程, BLCUP) ─────────────────
LESSON_TITLES: dict[tuple[str, int], tuple[str, str, str]] = {
    # (level, lesson_number): (title_zh, title_en, topic)
    # ── HSK 4A ── lessons 1-10 (第四册上)
    ("HSK4", 1):  ("第1课 你了解中国的节日吗",  "Lesson 1: Do You Know Chinese Festivals?", "festivals"),
    ("HSK4", 2):  ("第2课 我来介绍一下",         "Lesson 2: Let Me Make an Introduction",     "introductions"),
    ("HSK4", 3):  ("第3课 我想在中国开家公司",   "Lesson 3: I Want to Open a Company in China", "business"),
    ("HSK4", 4):  ("第4课 我帮你联系",           "Lesson 4: I'll Contact Them for You",       "communication"),
    ("HSK4", 5):  ("第5课 你的兴趣爱好是什么",   "Lesson 5: What Are Your Hobbies?",          "hobbies"),
    ("HSK4", 6):  ("第6课 不同的饮食习惯",       "Lesson 6: Different Eating Habits",          "food"),
    ("HSK4", 7):  ("第7课 中国文化很有意思",     "Lesson 7: Chinese Culture Is Very Interesting", "culture"),
    ("HSK4", 8):  ("第8课 运动的好处",           "Lesson 8: The Benefits of Exercise",         "health"),
    ("HSK4", 9):  ("第9课 你怎么看",             "Lesson 9: What Do You Think?",               "opinions"),
    ("HSK4", 10): ("第10课 我的中国朋友",        "Lesson 10: My Chinese Friend",               "friendship"),
    # ── HSK 4B ── lessons 11-20 (第四册下)
    ("HSK4", 11): ("第11课 买东西",              "Lesson 11: Shopping",                        "shopping"),
    ("HSK4", 12): ("第12课 旅游",                "Lesson 12: Travel",                          "travel"),
    ("HSK4", 13): ("第13课 面试",                "Lesson 13: Job Interview",                   "work"),
    ("HSK4", 14): ("第14课 科技改变生活",        "Lesson 14: Technology Changes Life",         "technology"),
    ("HSK4", 15): ("第15课 保护环境",            "Lesson 15: Protecting the Environment",      "environment"),
    ("HSK4", 16): ("第16课 父母与孩子",          "Lesson 16: Parents and Children",            "family"),
    ("HSK4", 17): ("第17课 中国的传统节日",      "Lesson 17: Traditional Chinese Holidays",    "traditions"),
    ("HSK4", 18): ("第18课 我们的城市",          "Lesson 18: Our City",                        "city life"),
    ("HSK4", 19): ("第19课 健康生活",            "Lesson 19: Healthy Living",                  "health"),
    ("HSK4", 20): ("第20课 综合复习",            "Lesson 20: Comprehensive Review",            "review"),
}

# ── answer key PDFs ───────────────────────────────────────────────────────────
ANSWER_KEYS = {
    # lesson_number → (pdf_filename, page_range_hint)
    # HSK 4A answers: lessons 1-10
    **{i: ("新HSK教程4上 Answers @hanyu_uz.pdf", "") for i in range(1, 11)},
    # HSK 4B answers: lessons 11-20
    **{i: ("新HSK教程4下Answers@hanyu_uz.pdf", "") for i in range(11, 21)},
}

# ── volume assignment ─────────────────────────────────────────────────────────
def lesson_volume(level: str, lesson_num: int) -> str:
    if level == "HSK4":
        return "A" if lesson_num <= 10 else "B"
    return ""

# ── filename parser ───────────────────────────────────────────────────────────
# Matches:  "3-5.mp3"  or  "2--1.mp3"  (double dash quirk in lesson 2)
_FNAME_RE = re.compile(r"^(\d+)-{1,2}(\d+)\.mp3$", re.IGNORECASE)

def parse_track(fname: str):
    """Return (lesson_int, section_int) or None."""
    m = _FNAME_RE.match(fname)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))

# ── scan audio_extracted ──────────────────────────────────────────────────────
def scan_audio() -> dict:
    """
    Returns:
      {
        "HSK4": {
          lesson_number: {
            section_number: "relative/path/to/file.mp3"  # relative to AUDIO_DIR
          }
        }
      }
    """
    result: dict[str, dict[int, dict[int, str]]] = {}

    if not AUDIO_DIR.exists():
        print(f"[WARN] audio_extracted/ not found at {AUDIO_DIR}")
        return result

    for mp3 in sorted(AUDIO_DIR.rglob("*.mp3")):
        parsed = parse_track(mp3.name)
        if parsed is None:
            print(f"  [skip] unrecognised filename: {mp3.name}")
            continue

        lesson_num, section_num = parsed

        # Determine level from directory name heuristics
        rel = mp3.relative_to(AUDIO_DIR)
        rel_parts = str(rel).replace("\\", "/")

        if "4上" in rel_parts or "4上" in str(mp3):
            level = "HSK4"
        elif "4下" in rel_parts or "4下" in str(mp3) or (lesson_num >= 11 and lesson_num <= 20):
            level = "HSK4"
        elif "HSK3" in rel_parts or "3" in rel_parts.split("/")[0]:
            level = "HSK3"
        elif "HSK2" in rel_parts or "2" in rel_parts.split("/")[0]:
            level = "HSK2"
        elif "HSK1" in rel_parts or "1" in rel_parts.split("/")[0]:
            level = "HSK1"
        else:
            # Fallback: guess from lesson number
            level = "HSK4"

        # Store relative path from AUDIO_DIR (use forward slashes)
        rel_path = str(mp3.relative_to(AUDIO_DIR)).replace("\\", "/")

        result.setdefault(level, {}).setdefault(lesson_num, {})[section_num] = rel_path

    return result

# ── build manifest ────────────────────────────────────────────────────────────
def build_manifest(audio_data: dict) -> list[dict]:
    entries = []

    for level, lessons in sorted(audio_data.items()):
        for lesson_num in sorted(lessons.keys()):
            sections = lessons[lesson_num]
            volume = lesson_volume(level, lesson_num)

            # Build audio track list (sections 1-8)
            tracks = []
            for sec_num in range(1, 9):
                if sec_num not in sections:
                    continue  # skip missing sections
                section_key, label_zh, label_en = SECTION_MAP[sec_num]
                tracks.append({
                    "section":    section_key,
                    "label_zh":   label_zh,
                    "label":      label_en,
                    "track":      sections[sec_num],  # relative to audio_extracted/
                    "duration_s": 0,                  # filled by player at runtime
                })

            # Lesson titles
            title_zh, title_en, topic = LESSON_TITLES.get(
                (level, lesson_num),
                (f"第{lesson_num}课", f"Lesson {lesson_num}", ""),
            )

            # Answer key
            ak_pdf, ak_pages = ANSWER_KEYS.get(lesson_num, (None, ""))

            entry = {
                "hsk_level":       level,
                "book":            "textbook",
                "volume":          volume,
                "lesson_number":   lesson_num,
                "title_zh":        title_zh,
                "title_en":        title_en,
                "topic":           topic,
                "audio_tracks":    tracks,
                "answer_key_pdf":  ak_pdf,
                "answer_key_pages": ak_pages,
            }
            entries.append(entry)

    return entries

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Scanning {AUDIO_DIR} …")
    audio_data = scan_audio()

    total_tracks = sum(
        len(secs)
        for lvl in audio_data.values()
        for secs in lvl.values()
    )
    print(f"  Found {total_tracks} audio tracks across "
          f"{sum(len(v) for v in audio_data.values())} lessons "
          f"in {len(audio_data)} levels.")

    manifest = build_manifest(audio_data)
    print(f"  Built {len(manifest)} lesson entries.")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✓ Written → {OUT_FILE}")
    print()
    print("Next step: POST /api/v1/course/lessons/seed")
    print("  curl -X POST http://localhost:8000/api/v1/course/lessons/seed")

if __name__ == "__main__":
    sys.exit(main() or 0)

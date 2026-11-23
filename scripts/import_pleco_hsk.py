"""Merge a Pleco Chinese flashcard export into the app's HSK 3.0 vocabulary.

    python scripts/import_pleco_hsk.py "path/to/HSK3.0 flashCARDS.xml"

The import includes cards assigned to HSK levels 1-9. Existing syllabus levels
stay authoritative; Pleco definitions are appended to matching words and additional
readings are retained. Levels 7-9 are represented by one HSK7-9 band because the
app's learning model has one advanced band. The existing dataset is backed up
before any change. This only updates the JSON seed file; run
scripts/import_hsk.py afterwards to refresh a configured database.
"""
import argparse
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT
sys.path.insert(0, str(BACKEND))
from services.pinyin_service import numeric_to_tone_marks, tone_marks_to_numeric  # noqa: E402

DATA = BACKEND / "data" / "hsk" / "hsk30.json"
LEVEL_RE = re.compile(r"HSK 3\.0(?: \(2026\))?/Level ([1-6])$")
ADVANCED_RE = re.compile(r"HSK 3\.0(?: \(2026\))?/Level 7-9$")


def norm_pinyin(pinyin: str) -> str:
    # Pleco marks syllable boundaries with `//`; the bundled syllabus sometimes
    # omits spaces, so normalize both representations before comparing.
    pinyin = re.sub(r"[/\s-]+", "", pinyin)
    return re.sub(r"[\s5]", "", tone_marks_to_numeric(pinyin).lower().replace("u:", "ü").replace("v", "ü"))


def plain_hanzi(value: str) -> str:
    return "".join(ch for ch in value if "\u3400" <= ch <= "\u9fff" or ch in "〇〡〢〣〤〥〦〧〨〩")


def get_text(parent, tag):
    node = parent.find(tag)
    return (node.text or "").strip() if node is not None else ""


def pleco_words(xml_path: Path):
    root = ET.parse(xml_path).getroot()
    words = {}
    excluded = Counter()
    for card in root.findall("./cards/card"):
        level_categories = [m.group(1) for assignment in card.findall("catassign")
                            if (m := LEVEL_RE.fullmatch(assignment.get("category", "")))]
        has_advanced_category = any(ADVANCED_RE.fullmatch(a.get("category", ""))
                                    for a in card.findall("catassign"))
        if not level_categories and not has_advanced_category:
            excluded["no HSK 3.0 level 1-9 assignment"] += 1
            continue
        categories = sorted(set(level_categories), key=int)
        if has_advanced_category:
            categories.append("7-9")
        entry = card.find("entry")
        if entry is None:
            excluded["missing entry"] += 1
            continue
        simplified = next((h.text.strip() for h in entry.findall("headword")
                           if h.get("charset") == "sc" and h.text), "")
        traditional = next((h.text.strip() for h in entry.findall("headword")
                            if h.get("charset") == "tc" and h.text), simplified)
        numeric = get_text(entry, "pron")
        try:
            pinyin = numeric_to_tone_marks(numeric)
            key = (simplified, norm_pinyin(pinyin))
        except (ValueError, TypeError):
            excluded["invalid pinyin"] += 1
            continue
        if not simplified or not pinyin:
            excluded["missing headword or pinyin"] += 1
            continue
        raw_definition = get_text(entry, "defn")
        definition = " ".join(raw_definition.split())
        if not definition:
            definition = "(definition unavailable in source export)"
        data = words.setdefault(key, {
            "simplified": simplified,
            "traditional": traditional,
            "pinyin": pinyin,
            "definitions": [],
            "source": "Pleco User -1; Pleco 2.0 Flashcard Exporter; HSK 3.0, levels 1-9",
            "source_category_levels": categories,
        })
        if definition and definition not in data["definitions"]:
            data["definitions"].append(definition)
    return words, excluded


def merge(xml_path: Path, backup=True):
    current = json.loads(DATA.read_text(encoding="utf-8"))
    incoming, excluded = pleco_words(xml_path)
    index = {(w["simplified"], norm_pinyin(w["pinyin"])): w for w in current}
    stats = Counter()
    # The standard HSK builder stores tone-number pinyin. Backfill it for rows
    # added by this import and repair rare source cards that carry no definition.
    for row in current:
        row["pinyin_numeric"] = tone_marks_to_numeric(row["pinyin"])
        if not row["definitions"]:
            row["definitions"] = ["(definition unavailable in source export)"]
            stats["missing_definitions_repaired"] += 1
    for key, card in incoming.items():
        row = index.get(key)
        if row:
            stats["matched"] += 1
            for definition in card["definitions"]:
                if definition not in row["definitions"]:
                    row["definitions"].append(definition)
                    stats["definitions_added"] += 1
            # Never overwrite current official syllabus levels. Record where the
            # source independently places this card for review and provenance.
            row.setdefault("source_data", {})["pleco_hsk_2026_levels"] = card["source_category_levels"]
            row.setdefault("sources", []).append("Pleco User -1; Pleco 2.0 Flashcard Exporter") \
                if "Pleco User -1; Pleco 2.0 Flashcard Exporter" not in row.get("sources", []) else None
        else:
            row = {
                "simplified": card["simplified"],
                "traditional": card["traditional"],
                "pinyin": card["pinyin"],
                "pinyin_numeric": tone_marks_to_numeric(card["pinyin"]),
                "pos": "",
                "definitions": card["definitions"],
                "hsk_level": "HSK7-9" if "7-9" in card["source_category_levels"]
                    else "HSK" + card["source_category_levels"][0],
                "syllabus_seq": None,
                "frequency_rank": None,
                "definition_quality": "pleco_import",
                "sources": ["Pleco User -1; Pleco 2.0 Flashcard Exporter"],
                "source_data": {"pleco_hsk_2026_levels": card["source_category_levels"]},
            }
            current.append(row)
            index[key] = row
            stats["new_readings"] += 1
    if backup:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = DATA.with_name(f"hsk30.json.backup-{stamp}")
        shutil.copy2(DATA, backup_path)
    DATA.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats, excluded, len(incoming), len(current)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=Path, help="Pleco XML flashcard export")
    parser.add_argument("--dry-run", action="store_true", help="show counts without changing files")
    args = parser.parse_args()
    incoming, excluded = pleco_words(args.xml)
    if args.dry_run:
        current = json.loads(DATA.read_text(encoding="utf-8"))
        index = {(w["simplified"], norm_pinyin(w["pinyin"])): w for w in current}
        matched = sum(key in index for key in incoming)
        print(f"Pleco cards assigned to HSK 3.0 levels 1-9: {len(incoming)}")
        print(f"Match current vocabulary: {matched}; new word/readings: {len(incoming)-matched}")
        print(f"Excluded: {sum(excluded.values())} ({dict(excluded)})")
        return
    stats, excluded, count, total = merge(args.xml)
    print(f"Done: {count} Pleco cards merged; {stats['matched']} existing rows matched; "
          f"{stats['definitions_added']} definitions added; {stats['new_readings']} new readings; "
          f"{total} total entries. Excluded: {dict(excluded)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Seed HSK 3.0 section-based test questions into the database.

Usage:
    docker compose exec backend python /app/scripts/seed_hsk30_tests.py
    docker compose exec backend python /app/scripts/seed_hsk30_tests.py --level HSK1
    docker compose exec backend python /app/scripts/seed_hsk30_tests.py --dry-run
    docker compose exec backend python /app/scripts/seed_hsk30_tests.py --clear-first
"""
import asyncio
import json
import sys
import os
import argparse
from pathlib import Path

# ── path setup ──────────────────────────────────────────────────────────────
# Allow running from repo root or from /app inside Docker
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

DATA_FILE = BASE_DIR / "backend" / "data" / "tests" / "hsk30_questions.json"

# ── DB imports (backend package) ────────────────────────────────────────────
from sqlalchemy import text, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


def get_db_url() -> str:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://chines_user:chines_pass@localhost:5432/chines_db",
    )
    # Normalise: ensure asyncpg driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


SECTION_ORDER = {"listening": 0, "reading": 1, "writing": 2}

VALID_LEVELS   = {"HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6", "HSK7", "HSK8", "HSK9"}
VALID_SECTIONS = set(SECTION_ORDER)
VALID_TYPES    = {"vocabulary", "pinyin", "fill_blank", "listening", "reading", "writing"}
VALID_OPTIONS  = {"A", "B", "C", "D"}


# ── validation ───────────────────────────────────────────────────────────────
def validate_question(q: dict, idx: int) -> list[str]:
    errs = []
    for field in ("hsk_level", "section", "question_type", "question_text",
                  "option_a", "option_b", "option_c", "correct_option", "explanation"):
        if not q.get(field):
            errs.append(f"[{idx}] missing '{field}'")

    if q.get("hsk_level") not in VALID_LEVELS:
        errs.append(f"[{idx}] bad hsk_level: {q.get('hsk_level')}")
    if q.get("section") not in VALID_SECTIONS:
        errs.append(f"[{idx}] bad section: {q.get('section')}")
    if q.get("question_type") not in VALID_TYPES:
        errs.append(f"[{idx}] bad question_type: {q.get('question_type')}")
    if q.get("correct_option") not in VALID_OPTIONS:
        errs.append(f"[{idx}] bad correct_option: {q.get('correct_option')}")

    # If correct_option is D, option_d must be present
    if q.get("correct_option") == "D" and not q.get("option_d"):
        errs.append(f"[{idx}] correct_option=D but option_d is null")

    return errs


# ── upsert logic ─────────────────────────────────────────────────────────────
async def seed(
    level_filter: str | None = None,
    dry_run: bool = False,
    clear_first: bool = False,
) -> None:
    print(f"\n{'[DRY RUN] ' if dry_run else ''}HSK 3.0 Test Question Seeder")
    print("=" * 60)

    # 1. Load JSON
    with open(DATA_FILE, encoding="utf-8") as f:
        raw: list[dict] = json.load(f)
    print(f"Loaded {len(raw)} questions from {DATA_FILE.name}")

    # 2. Filter by level if requested
    if level_filter:
        raw = [q for q in raw if q["hsk_level"] == level_filter.upper()]
        print(f"Filtered to {level_filter}: {len(raw)} questions")

    # 3. Validate all
    all_errors: list[str] = []
    for i, q in enumerate(raw):
        all_errors.extend(validate_question(q, i))
    if all_errors:
        print(f"\n❌ Validation errors ({len(all_errors)}):")
        for e in all_errors:
            print(f"   {e}")
        sys.exit(1)
    print(f"✓ All {len(raw)} questions validated")

    if dry_run:
        from collections import Counter
        counts = Counter((q["hsk_level"], q["section"]) for q in raw)
        print("\nDry-run summary (would insert/update):")
        for (lvl, sec), cnt in sorted(counts.items()):
            print(f"   {lvl:5s} {sec:10s}: {cnt}")
        return

    # 4. Connect to DB
    engine = create_async_engine(get_db_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 5. Optionally clear HSK3.0-tagged rows first
        if clear_first:
            levels = {q["hsk_level"] for q in raw}
            for lvl in sorted(levels):
                result = await db.execute(
                    text(
                        "DELETE FROM hsk_test_questions "
                        "WHERE hsk_level = :lvl AND section IS NOT NULL"
                    ),
                    {"lvl": lvl},
                )
                print(f"  Cleared {result.rowcount} existing rows for {lvl}")
            await db.commit()

        # 6. Upsert each question
        inserted = updated = skipped = 0
        for q in raw:
            # Build upsert: check by (hsk_level, section, question_number)
            check = await db.execute(
                text(
                    "SELECT id FROM hsk_test_questions "
                    "WHERE hsk_level = :lvl "
                    "  AND section   = :sec "
                    "  AND question_number = :qnum "
                    "LIMIT 1"
                ),
                {
                    "lvl": q["hsk_level"],
                    "sec": q["section"],
                    "qnum": q.get("question_number", 0),
                },
            )
            row = check.fetchone()

            params = {
                "lvl":       q["hsk_level"],
                "sec":       q["section"],
                "qnum":      q.get("question_number", 0),
                "qtype":     q["question_type"],
                "qtext":     q["question_text"],
                "opt_a":     q["option_a"],
                "opt_b":     q["option_b"],
                "opt_c":     q["option_c"],
                "opt_d":     q.get("option_d"),
                "correct":   q["correct_option"],
                "explain":   q.get("explanation", ""),
                "audio":     q.get("audio_path"),
                "image":     q.get("image_url"),
                "pass_id":   q.get("passage_id"),
                "pass_text": q.get("passage_text"),
            }

            if row:
                await db.execute(
                    text("""
                        UPDATE hsk_test_questions SET
                            question_type   = :qtype,
                            question_text   = :qtext,
                            option_a        = :opt_a,
                            option_b        = :opt_b,
                            option_c        = :opt_c,
                            option_d        = :opt_d,
                            correct_option  = :correct,
                            explanation     = :explain,
                            audio_path      = :audio,
                            image_url       = :image,
                            passage_id      = :pass_id,
                            passage_text    = :pass_text
                        WHERE hsk_level       = :lvl
                          AND section         = :sec
                          AND question_number = :qnum
                    """),
                    params,
                )
                updated += 1
            else:
                await db.execute(
                    text("""
                        INSERT INTO hsk_test_questions
                            (hsk_level, section, question_number, question_type,
                             question_text, option_a, option_b, option_c, option_d,
                             correct_option, explanation, audio_path, image_url,
                             passage_id, passage_text)
                        VALUES
                            (:lvl, :sec, :qnum, :qtype,
                             :qtext, :opt_a, :opt_b, :opt_c, :opt_d,
                             :correct, :explain, :audio, :image,
                             :pass_id, :pass_text)
                    """),
                    params,
                )
                inserted += 1

        await db.commit()

    await engine.dispose()

    print(f"\n✅ Done!")
    print(f"   Inserted : {inserted}")
    print(f"   Updated  : {updated}")
    print(f"   Skipped  : {skipped}")
    print(f"   Total    : {inserted + updated + skipped}")


# ── entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed HSK 3.0 test questions")
    parser.add_argument("--level",       help="Only seed specific level, e.g. HSK1")
    parser.add_argument("--dry-run",     action="store_true", help="Validate & summarise only")
    parser.add_argument("--clear-first", action="store_true",
                        help="Delete existing rows for the selected levels before inserting")
    args = parser.parse_args()

    asyncio.run(
        seed(
            level_filter=args.level,
            dry_run=args.dry_run,
            clear_first=args.clear_first,
        )
    )

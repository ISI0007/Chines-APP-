"""
Seed/refresh the words table from backend/data/hsk/hsk30.json (official HSK 3.0, levels 1-6).

    python scripts/import_hsk.py            # add new words, update existing ones
    python scripts/import_hsk.py --prune    # also delete words no longer in the file

A word is identified by (simplified, pinyin), so heteronyms such as 行 xíng / 行 háng are separate
cards. Idempotent. --prune cascades to users' review progress for the removed words, so use it
when migrating old test data, not on a database with real learners' progress you want to keep.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT  # in Docker, /app is backend/
sys.path.insert(0, str(BACKEND))  # backend modules use bare imports (core., db., models.)

from sqlalchemy import delete, select  # noqa: E402
from db.database import AsyncSessionLocal, init_db  # noqa: E402
import models.user, models.vocabulary  # noqa: E401,E402,F401
from models.user import HskLevel  # noqa: E402
from models.vocabulary import Word  # noqa: E402
from services.pinyin_service import tone_marks_to_numeric  # noqa: E402

DATA = BACKEND / "data" / "hsk" / "hsk30.json"


def load_words() -> dict[tuple[str, str], dict]:
    words: dict[tuple[str, str], dict] = {}
    for w in json.loads(DATA.read_text(encoding="utf-8")):
        key = (w["simplified"], w["pinyin"])
        if key in words:
            continue
        words[key] = {
            "simplified": w["simplified"],
            "traditional": w["traditional"],
            "pinyin": w["pinyin"],
            # Derived from the toned pinyin so the two forms can never disagree.
            "pinyin_numeric": tone_marks_to_numeric(w["pinyin"]),
            "definitions": json.dumps(w["definitions"], ensure_ascii=False),
            "hsk_level": HskLevel(w["hsk_level"]),
            "frequency_rank": w.get("frequency_rank"),
        }
    return words


async def main(prune: bool) -> None:
    await init_db()
    incoming = load_words()
    async with AsyncSessionLocal() as db:
        existing = {(w.simplified, w.pinyin): w for w in (await db.execute(select(Word))).scalars()}
        added = updated = 0
        for key, data in incoming.items():
            row = existing.get(key)
            if row:
                for k, v in data.items():
                    setattr(row, k, v)
                updated += 1
            else:
                db.add(Word(**data))
                added += 1
        pruned = 0
        if prune:
            stale = [w.id for k, w in existing.items() if k not in incoming]
            if stale:
                await db.execute(delete(Word).where(Word.id.in_(stale)))
            pruned = len(stale)
        await db.commit()
    stale_left = 0 if prune else len([k for k in existing if k not in incoming])
    print(f"Done: {added} added, {updated} updated, {pruned} pruned, {len(incoming)} words in file."
          + (f" {stale_left} old words not in the file remain (run with --prune to remove)." if stale_left else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prune", action="store_true")
    asyncio.run(main(ap.parse_args().prune))

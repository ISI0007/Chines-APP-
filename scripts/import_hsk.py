"""
Seed/refresh the words table from backend/data/hsk/hsk{1..6}.json.

Run from repo root (or inside the backend container):
    python scripts/import_hsk.py

Idempotent: matches existing rows by `simplified`, updates them, inserts the rest.
A word listed in several levels keeps its LOWEST level.
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT  # in Docker, /app is backend/
sys.path.insert(0, str(BACKEND))  # backend modules use bare imports (core., db., models.)

from sqlalchemy import select  # noqa: E402
from db.database import AsyncSessionLocal, init_db  # noqa: E402
import models.user, models.vocabulary  # noqa: E401,E402,F401
from models.user import HskLevel  # noqa: E402
from models.vocabulary import Word  # noqa: E402
from services.pinyin_service import tone_marks_to_numeric  # noqa: E402

HSK_DIR = BACKEND / "data" / "hsk"
RANK_BASE = {1: 0, 2: 150}  # HSK3+ files already carry ranks starting at 301


def load_words() -> dict[str, dict]:
    words: dict[str, dict] = {}
    for n in range(1, 7):
        path = HSK_DIR / f"hsk{n}.json"
        if not path.exists():
            print(f"  skip hsk{n}.json (missing)")
            continue
        for i, w in enumerate(json.loads(path.read_text(encoding="utf-8"))):
            if w["simplified"] in words:  # lower level already claimed it
                continue
            # HSK1/2 files carry no rank; use file order so NULLs don't sort after HSK3-6.
            rank = w.get("frequency_rank") or (RANK_BASE.get(n, 0) + i + 1)
            words[w["simplified"]] = {
                "simplified": w["simplified"],
                "traditional": w.get("traditional") or w["simplified"],
                "pinyin": w["pinyin"],
                # Derived from the toned pinyin so the two forms can never disagree.
                "pinyin_numeric": tone_marks_to_numeric(w["pinyin"]),
                "definitions": json.dumps(w["definitions"], ensure_ascii=False),
                "hsk_level": HskLevel(f"HSK{n}"),
                "frequency_rank": rank,
            }
    return words


async def main() -> None:
    await init_db()
    incoming = load_words()
    async with AsyncSessionLocal() as db:
        existing = {w.simplified: w for w in (await db.execute(select(Word))).scalars()}
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
        await db.commit()
    print(f"Done: {added} added, {updated} updated, {len(incoming)} unique words.")


if __name__ == "__main__":
    asyncio.run(main())

"""
HSK word importer — reads all JSON files in backend/data/hsk/
and upserts into the words table.

Usage:
    python scripts/import_hsk.py

Requires DATABASE_URL in .env (or environment).
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Allow running from repo root or scripts/ directory
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.db.database import engine, Base
from backend.models.vocabulary import Word
from backend.models.user import HskLevel

HSK_DIR = ROOT / "backend" / "data" / "hsk"

HSK_LEVEL_MAP = {
    "hsk1.json": HskLevel.HSK1,
    "hsk2.json": HskLevel.HSK2,
    "hsk3.json": HskLevel.HSK3,
    "hsk4.json": HskLevel.HSK4,
    "hsk5.json": HskLevel.HSK5,
    "hsk6.json": HskLevel.HSK6,
}


async def import_words() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    total = 0
    async with engine.begin() as conn:
        for filename, hsk_level in HSK_LEVEL_MAP.items():
            path = HSK_DIR / filename
            if not path.exists():
                print(f"  SKIP {filename} (not found)")
                continue

            with open(path, encoding="utf-8") as f:
                words = json.load(f)

            rows = []
            for w in words:
                definitions = w.get("definitions", [])
                defs_str = json.dumps(definitions, ensure_ascii=False)
                rows.append({
                    "simplified": w["simplified"],
                    "traditional": w.get("traditional", w["simplified"]),
                    "pinyin": w.get("pinyin", ""),
                    "pinyin_numeric": w.get("pinyin_numeric", ""),
                    "definitions": defs_str,
                    "hsk_level": hsk_level,
                    "frequency_rank": w.get("frequency_rank", 9999),
                    "audio_path": None,
                    "stroke_order_data": None,
                })

            if not rows:
                continue

            # PostgreSQL UPSERT — update on conflict (simplified)
            stmt = pg_insert(Word).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["simplified"],
                set_={
                    "traditional": stmt.excluded.traditional,
                    "pinyin": stmt.excluded.pinyin,
                    "pinyin_numeric": stmt.excluded.pinyin_numeric,
                    "definitions": stmt.excluded.definitions,
                    "hsk_level": stmt.excluded.hsk_level,
                    "frequency_rank": stmt.excluded.frequency_rank,
                },
            )
            await conn.execute(stmt)
            print(f"  ✓ {hsk_level.value}: {len(rows)} words upserted")
            total += len(rows)

    print(f"\nDone — {total} total words imported.")


if __name__ == "__main__":
    asyncio.run(import_words())

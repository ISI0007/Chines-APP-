"""
Script to import HSK 1-6 word lists into the database.
Run after docker-compose up:
    docker compose exec backend python /app/../scripts/import_hsk.py

Data source: Open HSK lists (public domain)
CC-CEDICT: https://www.mdbg.net/chinese/dictionary?page=cc-cedict (CC-BY-SA)
"""
import asyncio
import json
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

from db.database import AsyncSessionLocal, init_db
from models.vocabulary import Word

# Minimal HSK1 sample — replace with full list from open sources
HSK_SAMPLE = {
    "HSK1": [
        {"simplified": "你好", "traditional": "你好", "pinyin": "nǐ hǎo", "pinyin_numeric": "ni3 hao3", "definitions": ["hello", "hi", "how do you do"]},
        {"simplified": "谢谢", "traditional": "謝謝", "pinyin": "xiè xie", "pinyin_numeric": "xie4 xie5", "definitions": ["thank you", "thanks"]},
        {"simplified": "是", "traditional": "是", "pinyin": "shì", "pinyin_numeric": "shi4", "definitions": ["is", "are", "am", "yes"]},
        {"simplified": "不", "traditional": "不", "pinyin": "bù", "pinyin_numeric": "bu4", "definitions": ["not", "no"]},
        {"simplified": "我", "traditional": "我", "pinyin": "wǒ", "pinyin_numeric": "wo3", "definitions": ["I", "me", "my"]},
        {"simplified": "你", "traditional": "你", "pinyin": "nǐ", "pinyin_numeric": "ni3", "definitions": ["you (informal)"]},
        {"simplified": "他", "traditional": "他", "pinyin": "tā", "pinyin_numeric": "ta1", "definitions": ["he", "him"]},
        {"simplified": "她", "traditional": "她", "pinyin": "tā", "pinyin_numeric": "ta1", "definitions": ["she", "her"]},
        {"simplified": "们", "traditional": "們", "pinyin": "men", "pinyin_numeric": "men5", "definitions": ["plural marker for pronouns"]},
        {"simplified": "中国", "traditional": "中國", "pinyin": "Zhōng guó", "pinyin_numeric": "Zhong1 guo2", "definitions": ["China"]},
    ],
    "HSK2": [
        {"simplified": "但是", "traditional": "但是", "pinyin": "dàn shì", "pinyin_numeric": "dan4 shi4", "definitions": ["but", "however"]},
        {"simplified": "因为", "traditional": "因為", "pinyin": "yīn wèi", "pinyin_numeric": "yin1 wei4", "definitions": ["because", "owing to"]},
        {"simplified": "所以", "traditional": "所以", "pinyin": "suǒ yǐ", "pinyin_numeric": "suo3 yi3", "definitions": ["therefore", "so", "thus"]},
    ],
}


async def import_words():
    await init_db()
    async with AsyncSessionLocal() as db:
        count = 0
        for level, words in HSK_SAMPLE.items():
            for i, w in enumerate(words):
                word = Word(
                    simplified=w["simplified"],
                    traditional=w.get("traditional"),
                    pinyin=w["pinyin"],
                    pinyin_numeric=w.get("pinyin_numeric"),
                    definitions=json.dumps(w["definitions"], ensure_ascii=False),
                    hsk_level=level,
                    frequency_rank=i + 1,
                )
                db.add(word)
                count += 1
        await db.commit()
        print(f"✅ Imported {count} words")


if __name__ == "__main__":
    asyncio.run(import_words())

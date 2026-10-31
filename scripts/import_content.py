"""
Seed reading texts, grammar lessons and HSK test questions from backend/data/.

    python scripts/import_content.py

Idempotent: reading texts are matched by (hsk_level, title), grammar lessons by
(hsk_level, title), test questions by (hsk_level, question_text).
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT  # in Docker, /app is backend/
sys.path.insert(0, str(BACKEND))

from sqlalchemy import select  # noqa: E402
from db.database import AsyncSessionLocal, init_db  # noqa: E402
import models.user, models.vocabulary, models.reading, models.grammar, models.hsk_test  # noqa: E401,E402,F401
from models.user import HskLevel  # noqa: E402
from models.reading import ReadingText  # noqa: E402
from models.grammar import GrammarLesson  # noqa: E402
from models.hsk_test import HskTestQuestion, QuestionType  # noqa: E402

DATA = BACKEND / "data"


def _files(sub: str):
    return sorted((DATA / sub).glob("*.json"))


async def seed_reading(db):
    n = 0
    for f in _files("reading"):
        for t in json.loads(f.read_text(encoding="utf-8")):
            lvl = HskLevel(t["hsk_level"])
            hit = (await db.execute(select(ReadingText).where(
                ReadingText.hsk_level == lvl, ReadingText.title == t["title"]))).scalar_one_or_none()
            if hit:
                continue
            db.add(ReadingText(
                title=t["title"], title_pinyin=t.get("title_pinyin", ""), content=t["content"],
                content_pinyin=t.get("content_pinyin", ""), translation=t.get("translation", ""),
                hsk_level=lvl, topic=t.get("topic", ""), word_count=len(t["content"]),
            ))
            n += 1
    return n


async def seed_grammar(db):
    n = 0
    for f in _files("grammar"):
        for g in json.loads(f.read_text(encoding="utf-8")):
            lvl = HskLevel(g["hsk_level"])
            hit = (await db.execute(select(GrammarLesson).where(
                GrammarLesson.hsk_level == lvl, GrammarLesson.title == g["title"]))).scalar_one_or_none()
            if hit:
                continue
            db.add(GrammarLesson(
                title=g["title"], hsk_level=lvl, pattern=g["pattern"], explanation=g["explanation"],
                examples=json.dumps(g["examples"], ensure_ascii=False), order_index=g.get("order_index", 0),
            ))
            n += 1
    return n


async def seed_questions(db):
    n = 0
    for f in _files("tests"):
        lvl = HskLevel(f.stem.split("_")[0].upper())  # hsk1_questions.json -> HSK1
        for q in json.loads(f.read_text(encoding="utf-8")):
            hit = (await db.execute(select(HskTestQuestion).where(
                HskTestQuestion.hsk_level == lvl,
                HskTestQuestion.question_text == q["question_text"]))).scalar_one_or_none()
            if hit:
                continue
            db.add(HskTestQuestion(
                hsk_level=lvl, question_type=QuestionType(q["question_type"]),
                question_text=q["question_text"], option_a=q["option_a"], option_b=q["option_b"],
                option_c=q["option_c"], option_d=q["option_d"], correct_option=q["correct_option"],
                explanation=q.get("explanation", ""),
            ))
            n += 1
    return n


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        r, g, q = await seed_reading(db), await seed_grammar(db), await seed_questions(db)
        await db.commit()
    print(f"Added: {r} reading texts, {g} grammar lessons, {q} test questions.")


if __name__ == "__main__":
    asyncio.run(main())

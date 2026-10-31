from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from models.vocabulary import Word
from api.deps import current_user
from models.user import User

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("/words")
async def get_words(
    hsk_level: str = Query(None, description="Filter by HSK level e.g. HSK1"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(current_user),
):
    q = select(Word)
    if hsk_level:
        q = q.where(Word.hsk_level == hsk_level)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    words = result.scalars().all()
    return {"words": [
        {
            "id": w.id,
            "simplified": w.simplified,
            "traditional": w.traditional,
            "pinyin": w.pinyin,
            "definitions": w.definitions,
            "hsk_level": w.hsk_level,
            "audio_path": w.audio_path,
        }
        for w in words
    ], "total": len(words)}


@router.get("/words/{word_id}")
async def get_word(
    word_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(current_user),
):
    result = await db.execute(select(Word).where(Word.id == word_id))
    word = result.scalar_one_or_none()
    if not word:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Word not found")
    return word

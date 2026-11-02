"""
HSK 3.0 nine-band progression endpoint.

GET  /api/v1/progression   — current user's progress across all 9 HSK bands

Bands map to HSK 3.0 vocabulary counts:
  Band 1: 500 words    (≈ HSK 1)
  Band 2: 772 words    (≈ HSK 2)
  Band 3: 973 words    (≈ HSK 3)
  Band 4: 1000 words   (≈ HSK 4)
  Band 5: 1071 words   (≈ HSK 5)
  Band 6: 1140 words   (≈ HSK 6)
  Bands 7-9 share an upper range of ~5000 additional words (9-level spec)

Words_mastered is derived from the UserWordProgress SRS records.
Bands 1-6 unlock sequentially; bands 7-9 require band-6 completion.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.user import User

router = APIRouter(prefix="/progression", tags=["progression"])

# ── Band definitions ──────────────────────────────────────────────────────────

BAND_THRESHOLDS = {
    1: 500,
    2: 772,
    3: 973,
    4: 1000,
    5: 1071,
    6: 1140,
    7: 2000,
    8: 3500,
    9: 5000,
}

LEVEL_BAND_MAP = {
    "HSK1": 1,
    "HSK2": 2,
    "HSK3": 3,
    "HSK4": 4,
    "HSK5": 5,
    "HSK6": 6,
}


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class BandInfo(BaseModel):
    band:           int
    status:         str   # locked | in_progress | completed
    words_mastered: int
    words_total:    int
    pct:            float


class ProgressionResponse(BaseModel):
    current_band:   int
    bands:          list[BandInfo]


# ── Route ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=ProgressionResponse)
async def get_progression(
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Return the user's HSK 3.0 nine-band progression.

    Mastery counts come from UserWordProgress (is_learned=True).
    Bands are unlocked sequentially — band N+1 unlocks when band N is completed.
    """
    # Import here to avoid circular imports (vocabulary model)
    from models.vocabulary import UserWordProgress, Word

    # Count learned words per HSK level (1-6 map to bands 1-6)
    result = await db.execute(
        select(Word.hsk_level, func.count(UserWordProgress.id))
        .join(Word, Word.id == UserWordProgress.word_id)
        .where(
            UserWordProgress.user_id == user.id,
            UserWordProgress.is_learned == True,
        )
        .group_by(Word.hsk_level)
    )
    mastered_by_level: dict[str, int] = {row[0].value: row[1] for row in result.all()}

    # Total words per level
    total_result = await db.execute(
        select(Word.hsk_level, func.count(Word.id)).group_by(Word.hsk_level)
    )
    total_by_level: dict[str, int] = {row[0].value: row[1] for row in total_result.all()}

    # Cumulative mastered (bands 1-6 are cumulative HSK totals)
    cumulative_mastered = 0
    level_names = ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6"]
    level_mastered: dict[int, int] = {}   # band → cumulative mastered at that band
    for i, lvl in enumerate(level_names, start=1):
        cumulative_mastered += mastered_by_level.get(lvl, 0)
        level_mastered[i] = cumulative_mastered

    # Bands 7-9: no SRS data yet → use 0
    for b in (7, 8, 9):
        level_mastered[b] = 0

    bands: list[BandInfo] = []
    current_band = 1

    for band in range(1, 10):
        threshold = BAND_THRESHOLDS[band]
        mastered  = level_mastered.get(band, 0)

        if mastered >= threshold:
            status = "completed"
            current_band = min(band + 1, 9)
        elif band == 1 or level_mastered.get(band - 1, 0) >= BAND_THRESHOLDS.get(band - 1, 0):
            status = "in_progress"
            current_band = band
        else:
            status = "locked"

        pct = round(min((mastered / threshold) * 100, 100.0), 1)
        bands.append(BandInfo(
            band=band,
            status=status,
            words_mastered=mastered,
            words_total=threshold,
            pct=pct,
        ))

    # Make sure current_band is the lowest non-completed band
    for b in bands:
        if b.status != "completed":
            current_band = b.band
            break

    return ProgressionResponse(current_band=current_band, bands=bands)

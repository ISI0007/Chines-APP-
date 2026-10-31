"""
Pydantic schemas for vocabulary and SRS review endpoints.
"""

import json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator

from models.user import HskLevel


class WordResponse(BaseModel):
    """Single word detail returned by the API."""
    id: int
    simplified: str
    traditional: str
    pinyin: str
    pinyin_numeric: str
    definitions: list[str]
    hsk_level: HskLevel
    frequency_rank: Optional[int] = None
    audio_path: Optional[str] = None
    stroke_order_data: Optional[str] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def resolve_audio(self):
        """Point audio_path at the local MP3 when one has been added under data/audio/."""
        if not self.audio_path:
            from services.audio_service import local_audio_path
            local = local_audio_path(self.simplified, self.hsk_level.value)
            if local:
                self.audio_path = f"/api/v1/{local}"
        return self

    @field_validator("definitions", mode="before")
    @classmethod
    def parse_definitions(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class WordListResponse(BaseModel):
    """Paginated list of words."""
    total: int
    skip: int
    limit: int
    words: list[WordResponse]


class UserWordProgressResponse(BaseModel):
    """SRS progress for a single word."""
    word_id: int
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review: datetime
    last_reviewed: Optional[datetime] = None
    is_learned: bool

    model_config = {"from_attributes": True}


class ReviewRequest(BaseModel):
    """Body for POST /vocabulary/review"""
    word_id: int
    quality: int  # 0-5 SM-2 quality rating

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v):
        if not 0 <= v <= 5:
            raise ValueError("quality must be 0-5")
        return v


class ReviewResponse(BaseModel):
    """Result of a submitted flashcard review."""
    word_id: int
    next_review: datetime
    interval_days: int
    ease_factor: float
    is_learned: bool
    xp_gained: int

"""
User-facing routes — leaderboard, profile updates.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.user import User
from schemas.auth import UserResponse
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])


# ── Response schemas ──────────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    hsk_level: str
    xp: int
    streak_days: int

    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    top: list[LeaderboardEntry]
    me: Optional[LeaderboardEntry] = None   # None if current user is already in top list


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def leaderboard(
    limit: int = Query(20, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Top-N users by XP.  Also returns the current user's rank if they fall outside the top list.

    Query params:
    - limit: how many top users to return (default 20, max 100)
    """
    # Top-N by XP
    result = await db.execute(
        select(User)
        .where(User.is_active == True)
        .order_by(User.xp.desc(), User.id.asc())
        .limit(limit)
    )
    top_users = result.scalars().all()

    top = [
        LeaderboardEntry(
            rank=i + 1,
            user_id=u.id,
            username=u.username,
            hsk_level=u.hsk_level.value if hasattr(u.hsk_level, "value") else str(u.hsk_level),
            xp=u.xp,
            streak_days=u.streak_days or 0,
        )
        for i, u in enumerate(top_users)
    ]

    # Check if current user is already in top list
    in_top = any(e.user_id == user.id for e in top)
    me_entry: Optional[LeaderboardEntry] = None

    if not in_top:
        # Count users with strictly more XP (rank = count + 1)
        rank_result = await db.execute(
            select(func.count()).where(
                User.is_active == True,
                User.xp > user.xp,
            )
        )
        rank = (rank_result.scalar() or 0) + 1
        me_entry = LeaderboardEntry(
            rank=rank,
            user_id=user.id,
            username=user.username,
            hsk_level=user.hsk_level.value if hasattr(user.hsk_level, "value") else str(user.hsk_level),
            xp=user.xp,
            streak_days=user.streak_days or 0,
        )

    return LeaderboardResponse(top=top, me=me_entry)


class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    hsk_level: str
    xp: int
    streak_days: int
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("/me/profile", response_model=ProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Return current user profile including avatar URL if set."""
    from models.phase3 import UserAvatar
    avatar_row = (await db.execute(
        select(UserAvatar).where(UserAvatar.user_id == user.id)
    )).scalar_one_or_none()

    avatar_url: Optional[str] = None
    if avatar_row:
        avatar_url = f"/static/avatars/{avatar_row.filename}"

    return ProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        hsk_level=user.hsk_level.value if hasattr(user.hsk_level, "value") else str(user.hsk_level),
        xp=user.xp,
        streak_days=user.streak_days or 0,
        avatar_url=avatar_url,
    )


@router.patch("/me/level", response_model=UserResponse)
async def update_level(
    hsk_level: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Update the current user's HSK level target."""
    from models.user import HskLevel
    try:
        user.hsk_level = HskLevel(hsk_level.upper())
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid HSK level: {hsk_level}")
    await db.commit()
    await db.refresh(user)
    return user

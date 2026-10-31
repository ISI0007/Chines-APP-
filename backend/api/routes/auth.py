from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse
from services.auth_service import register_user, login_user, refresh_tokens
from api.deps import current_user
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(data, db)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await login_user(data, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_tokens(data.refresh_token, db)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return user

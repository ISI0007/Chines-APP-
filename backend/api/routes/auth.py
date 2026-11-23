from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from email.message import EmailMessage
import smtplib
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from services.auth_service import register_user, login_user, refresh_tokens, request_password_reset, reset_password
from api.deps import current_user
from models.user import User
from core.config import settings

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


def _send_reset_email(email: str, token: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Reset your ChineseLearn password"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(f"Use this one-time link within {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes to reset your password:\n\n{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}\n")
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    token = await request_password_reset(str(data.email), db)
    # Keep the response identical for known and unknown addresses to avoid account enumeration.
    result = {"message": "If the account exists, password reset instructions have been sent."}
    if token and settings.SMTP_HOST and settings.SMTP_FROM_EMAIL:
        try:
            await run_in_threadpool(_send_reset_email, str(data.email), token)
        except (OSError, smtplib.SMTPException):
            raise HTTPException(status_code=503, detail="Password reset email could not be sent. Try again later.")
    elif token and settings.APP_ENV != "production":
        result["reset_token"] = token
    return result


@router.post("/reset-password")
async def reset_password_route(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    if not await reset_password(data.token, data.new_password, db):
        raise HTTPException(status_code=400, detail="This reset link is invalid or expired. Request a new one.")
    return {"message": "Password updated. You can now sign in."}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(current_user)):
    return user

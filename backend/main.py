"""
Chinese Language Learning App — FastAPI backend
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.db.database import init_db
from backend.api.routes.auth import router as auth_router
from backend.api.routes.vocabulary import router as vocab_router
from backend.api.routes.audio import router as audio_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Chinese language learning app",
    version="0.2.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = [
    "http://localhost:19006",   # Expo web dev
    "http://localhost:3000",    # Web fallback
    "http://localhost:8081",    # Expo metro bundler
    "exp://localhost:19000",    # Expo Go
]
if settings.FRONTEND_URL:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(vocab_router, prefix="/api/v1")
app.include_router(audio_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "0.2.0"}

"""Chinese Language Learning App — FastAPI backend (run from backend/: uvicorn main:app)."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from db.database import init_db

# Import every model so Base.metadata.create_all() sees all tables.
import models.user, models.vocabulary, models.reading, models.grammar  # noqa: E401,F401
import models.hsk_test, models.writing, models.course, models.phase3   # noqa: E401,F401

from api.routes.auth import router as auth_router
from api.routes.vocabulary import router as vocab_router
from api.routes.audio import router as audio_router
from api.routes.reading import router as reading_router
from api.routes.grammar import router as grammar_router
from api.routes.tests import router as tests_router
from api.routes.writing import router as writing_router
from api.routes.users import router as users_router
from api.routes.course import router as course_router
# Phase 3 routers
from api.routes.shadowing import router as shadowing_router
from api.routes.avatar import router as avatar_router
from api.routes.course_progress import router as course_progress_router
from api.routes.listening_test import router as listening_test_router
from api.routes.progression import router as progression_router

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "avatars").mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Chinese language learning app",
    version="0.4.0",
    lifespan=lifespan,
)

# Serve avatar uploads
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

origins = [
    settings.FRONTEND_URL,
    "http://localhost:19006",  # Expo web
    "http://localhost:8081",   # Metro bundler
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    auth_router, vocab_router, audio_router, reading_router,
    grammar_router, tests_router, writing_router, users_router,
    course_router,
    # Phase 3
    shadowing_router, avatar_router, course_progress_router,
    listening_test_router, progression_router,
):
    app.include_router(r, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "0.4.0"}

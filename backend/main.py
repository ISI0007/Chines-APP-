"""Chinese Language Learning App — FastAPI backend (run from backend/: uvicorn main:app)."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.database import init_db

# Import every model so Base.metadata.create_all() sees all tables.
import models.user, models.vocabulary, models.reading, models.grammar, models.hsk_test  # noqa: E401,F401

from api.routes.auth import router as auth_router
from api.routes.vocabulary import router as vocab_router
from api.routes.audio import router as audio_router
from api.routes.reading import router as reading_router
from api.routes.grammar import router as grammar_router
from api.routes.tests import router as tests_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Chinese language learning app",
    version="0.3.0",
    lifespan=lifespan,
)

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

for r in (auth_router, vocab_router, audio_router, reading_router, grammar_router, tests_router):
    app.include_router(r, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "0.3.0"}

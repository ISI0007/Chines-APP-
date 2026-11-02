"""
Course lesson endpoints — HSK Standard Course (标准教程).

Routes
------
GET  /course/lessons               list lessons (filter by level + book)
GET  /course/lessons/{id}          single lesson with full audio track list
GET  /course/audio/{path}          serve an audio track (local assets only)
GET  /course/answer-key/{filename} serve an answer-key PDF (local assets only)
POST /course/lessons/seed          admin: load course_manifest.json into DB

Audio and answer-key files are served from the local filesystem
(backend/data/hsk_course_assets/).  They are NEVER committed to git —
see ASSETS_NOTICE.md.
"""
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.course import CourseBook, CourseLesson
from models.user import HskLevel

router = APIRouter(prefix="/course", tags=["course"])

# Path to local assets (not in git — see .gitignore)
ASSETS_DIR  = Path(__file__).resolve().parents[2] / "data" / "hsk_course_assets"
AUDIO_DIR   = ASSETS_DIR / "audio_extracted"
ANSWERS_DIR = ASSETS_DIR / "answer_keys"
MANIFEST    = ASSETS_DIR / "course_manifest.json"

# ── helpers ──────────────────────────────────────────────────────────────────

def _lesson_dict(lesson: CourseLesson) -> dict:
    return {
        "id":               lesson.id,
        "hsk_level":        lesson.hsk_level.value,
        "book":             lesson.book.value,
        "volume":           lesson.volume,
        "lesson_number":    lesson.lesson_number,
        "title_zh":         lesson.title_zh,
        "title_en":         lesson.title_en,
        "topic":            lesson.topic,
        "has_audio":        lesson.has_audio,
        "audio_tracks":     json.loads(lesson.audio_tracks or "[]"),
        "answer_key_pdf":   lesson.answer_key_pdf,
        "answer_key_pages": lesson.answer_key_pages,
    }


# ── list / detail ─────────────────────────────────────────────────────────────

@router.get("/lessons")
async def list_lessons(
    hsk_level: Optional[str] = Query(None, description="e.g. HSK1, HSK4"),
    book:      Optional[str] = Query(None, description="textbook | workbook"),
    volume:    Optional[str] = Query(None, description="A | B (for HSK4)"),
    db: AsyncSession = Depends(get_db),
):
    """Return lessons, ordered by lesson_number.  Strips audio_tracks payload for brevity."""
    stmt = select(CourseLesson).order_by(CourseLesson.lesson_number)

    if hsk_level:
        try:
            lvl = HskLevel(hsk_level.upper())
        except ValueError:
            raise HTTPException(400, f"Unknown hsk_level '{hsk_level}'")
        stmt = stmt.where(CourseLesson.hsk_level == lvl)

    if book:
        try:
            bk = CourseBook(book.lower())
        except ValueError:
            raise HTTPException(400, "book must be 'textbook' or 'workbook'")
        stmt = stmt.where(CourseLesson.book == bk)

    if volume is not None:
        stmt = stmt.where(CourseLesson.volume == volume.upper())

    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id":             r.id,
            "hsk_level":      r.hsk_level.value,
            "book":           r.book.value,
            "volume":         r.volume,
            "lesson_number":  r.lesson_number,
            "title_zh":       r.title_zh,
            "title_en":       r.title_en,
            "topic":          r.topic,
            "has_audio":      r.has_audio,
            "track_count":    len(json.loads(r.audio_tracks or "[]")),
            "answer_key_pdf": r.answer_key_pdf,
        }
        for r in rows
    ]


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        select(CourseLesson).where(CourseLesson.id == lesson_id)
    )).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Lesson not found")
    return _lesson_dict(row)


# ── audio file serving ────────────────────────────────────────────────────────

@router.get("/audio/{track_name:path}")
async def serve_audio(track_name: str):
    """
    Serve a single audio track.
    track_name is a path relative to audio_extracted/ (may contain subdirectories).
    Path traversal is blocked by resolving and checking the prefix.
    """
    # Block traversal attempts
    if ".." in track_name or track_name.startswith("/"):
        raise HTTPException(400, "Invalid track name")

    candidate = (AUDIO_DIR / track_name).resolve()
    # Ensure the resolved path stays inside AUDIO_DIR
    try:
        candidate.relative_to(AUDIO_DIR.resolve())
    except ValueError:
        raise HTTPException(400, "Invalid track name")

    if not candidate.exists():
        raise HTTPException(
            404,
            f"Audio track '{track_name}' not found. "
            "Run scripts/build_course_manifest.py to extract audio."
        )
    return FileResponse(candidate, media_type="audio/mpeg", headers={
        "Accept-Ranges": "bytes",  # enables seek in audio players
        "Cache-Control": "private, max-age=86400",
    })


# ── answer key PDF serving ────────────────────────────────────────────────────

@router.get("/answer-key/{filename}")
async def serve_answer_key(filename: str):
    """Serve an answer-key PDF from the local assets directory."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    if not filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are served here")

    path = ANSWERS_DIR / filename
    if not path.exists():
        raise HTTPException(
            404,
            f"Answer key '{filename}' not found in assets directory."
        )
    return FileResponse(path, media_type="application/pdf", headers={
        "Cache-Control": "private, max-age=86400",
    })


# ── seed from manifest ────────────────────────────────────────────────────────

@router.post("/lessons/seed")
async def seed_from_manifest(db: AsyncSession = Depends(get_db)):
    """
    Load (or refresh) course lessons from course_manifest.json.
    Safe to call repeatedly — upserts by (hsk_level, book, volume, lesson_number).
    """
    if not MANIFEST.exists():
        raise HTTPException(
            404,
            "course_manifest.json not found. "
            "Run: python scripts/build_course_manifest.py"
        )

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    inserted = updated = 0

    for entry in data:
        lvl  = HskLevel(entry["hsk_level"])
        book = CourseBook(entry.get("book", "textbook"))
        vol  = entry.get("volume", "")
        num  = int(entry["lesson_number"])

        hit = (await db.execute(
            select(CourseLesson).where(
                CourseLesson.hsk_level     == lvl,
                CourseLesson.book          == book,
                CourseLesson.volume        == vol,
                CourseLesson.lesson_number == num,
            )
        )).scalar_one_or_none()

        tracks = entry.get("audio_tracks", [])
        payload = dict(
            title_zh         = entry.get("title_zh", ""),
            title_en         = entry.get("title_en", ""),
            topic            = entry.get("topic", ""),
            audio_tracks     = json.dumps(tracks, ensure_ascii=False),
            has_audio        = len(tracks) > 0,
            answer_key_pdf   = entry.get("answer_key_pdf"),
            answer_key_pages = entry.get("answer_key_pages", ""),
        )

        if hit:
            for k, v in payload.items():
                setattr(hit, k, v)
            updated += 1
        else:
            db.add(CourseLesson(
                hsk_level=lvl, book=book, volume=vol, lesson_number=num, **payload
            ))
            inserted += 1

    await db.commit()
    return {"inserted": inserted, "updated": updated, "total": len(data)}

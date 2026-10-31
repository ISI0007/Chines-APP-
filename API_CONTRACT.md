# API Contract — Chinese Learning App
> **Backend branch:** `claude/backend`  
> **Base URL (local):** `http://localhost:8000/api/v1`  
> **Auth:** Bearer JWT in `Authorization` header

---

## Authentication

### Register
```
POST /api/v1/auth/register
Content-Type: application/json

{ "email": "user@example.com", "username": "student1", "password": "secret123" }

→ 201
{ "id": 1, "email": "user@example.com", "username": "student1",
  "hsk_level": "HSK1", "xp": 0, "streak_days": 0, "is_active": true }
```

### Login
```
POST /api/v1/auth/login

{ "email": "user@example.com", "password": "secret123" }

→ 200
{ "access_token": "<jwt>", "refresh_token": "<jwt>", "token_type": "bearer" }
```

### Refresh
```
POST /api/v1/auth/refresh

{ "refresh_token": "<jwt>" }

→ 200  { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### Current User
```
GET /api/v1/auth/me
Authorization: Bearer <access_token>

→ 200  { "id": 1, "email": "...", "username": "...", "hsk_level": "HSK1",
          "xp": 120, "streak_days": 3, "is_active": true }
```

---

## Vocabulary

### List Words
```
GET /api/v1/vocabulary/words?hsk_level=HSK1&skip=0&limit=50
Authorization: Bearer <token>

Query params:
  hsk_level  — HSK1 | HSK2 | HSK3 | HSK4 | HSK5 | HSK6  (optional)
  search     — substring match on simplified/pinyin/definitions  (optional)
  skip       — default 0
  limit      — default 50, max 200

→ 200
{
  "total": 300,
  "skip": 0,
  "limit": 50,
  "words": [
    {
      "id": 1,
      "simplified": "谢谢",
      "traditional": "謝謝",
      "pinyin": "xiè xie",
      "pinyin_numeric": "xie4 xie5",
      "definitions": ["to thank", "thanks", "thank you"],
      "hsk_level": "HSK1",
      "frequency_rank": 520,
      "audio_path": "/api/v1/audio/hsk1/谢谢.mp3",   ← null if no file
      "stroke_order_data": null
    }, ...
  ]
}
```

### Get Single Word
```
GET /api/v1/vocabulary/words/{word_id}
Authorization: Bearer <token>

→ 200  { same shape as word object above }
→ 404  { "detail": "Word not found" }
```

### Due-for-Review Words (SRS queue)
```
GET /api/v1/vocabulary/review?hsk_level=HSK1&limit=20
Authorization: Bearer <token>

Returns words the user should review now (next_review <= now)
plus brand-new words to fill up to `limit`.

→ 200  [ { word object }, ... ]
```

### Submit Review (SM-2)
```
POST /api/v1/vocabulary/review
Authorization: Bearer <token>

{ "word_id": 1, "quality": 4 }   ← quality 0-5

quality scale:
  0 = complete blackout
  1 = wrong, remembered when shown answer
  2 = wrong, seemed easy when shown
  3 = correct with difficulty
  4 = correct after hesitation
  5 = perfect recall

→ 200
{
  "word_id": 1,
  "next_review": "2026-11-07T10:00:00Z",
  "interval_days": 6,
  "ease_factor": 2.5,
  "is_learned": false,
  "xp_gained": 5          ← 5 if quality≥3, else 1
}
```

### Progress Summary
```
GET /api/v1/vocabulary/progress
Authorization: Bearer <token>

→ 200
{
  "user_xp": 120,
  "streak_days": 3,
  "levels": {
    "HSK1": { "total": 300, "learned": 42, "due_for_review": 8 },
    "HSK2": { "total": 300, "learned": 0,  "due_for_review": 0 },
    ...
  }
}
```

---

## Audio

### Serve Local MP3
```
GET /api/v1/audio/{hsk_level}/{filename}
Example: GET /api/v1/audio/hsk1/谢谢.mp3

→ 200  audio/mpeg stream
→ 404  { "detail": "Audio file not found" }
```

**Frontend audio strategy:**
1. If `word.audio_path` is not null, play `API_ORIGIN + word.audio_path` (a short human recording, ~1 s, `audio/mpeg`, served with Range support so a 206 reply is normal).
2. If it is null, fall back to synthetic speech (Google TTS URL below). It is an unofficial endpoint and can stop working; it also reads a multi-reading hanzi (e.g. 行) in only one way.
```js
`https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(simplified)}&tl=zh-CN&client=tw-ob`
```
**Recordings are real now** (open licence): `python scripts/fetch_audio.py` (run on the host, needs git + `pip install -r scripts/requirements-audio.txt`) downloads them into `backend/data/audio/` (not in git; the folder is mounted into Docker). Without that step `audio_path` stays null everywhere.
Coverage: **4,442 of 5,375 entries (83%)** — HSK1 93%, HSK2 87%, HSK3 91%, HSK4 84%, HSK5 85%, HSK6 76%. A word with several readings only gets a recording when the exact reading is known (single-syllable words).
Single-syllable recordings were checked against the expected tone with a pitch classifier (95% cross-validated accuracy on the labelled syllables, ~90% agreement on the word recordings); multi-syllable recordings are unchecked and rely on the source's curation. `backend/data/audio/MANIFEST.json` lists which recording backs which word.
**Attribution is required (CC BY-SA):** the About screen must credit *hugolpz/audio-cmn* (Shtooka/SWAC) — speakers Yue Tan (words) and Chen Wang (syllables). Text: `backend/data/audio/ATTRIBUTION.md`.

---

## Reading

```
GET  /api/v1/reading/texts?hsk_level=HSK1&topic=Family     -> [ReadingSummary]
GET  /api/v1/reading/texts/{id}                            -> ReadingDetail
POST /api/v1/reading/texts/{id}/complete  {"comprehension_score": 80}   (score optional, 0-100)

ReadingSummary: { id, title, title_pinyin, topic, hsk_level, word_count, completed }
ReadingDetail : ReadingSummary + { content, content_pinyin, translation, audio_path }
complete ->     { "xp_gained": 10, "total_xp": 10 }     // XP only on FIRST completion, else 0
```
`content_pinyin` is the whole passage in pinyin (sentence-level, not per-character alignment).

## Grammar

```
GET  /api/v1/grammar/lessons?hsk_level=HSK1   -> [{ id, title, hsk_level, pattern, order_index, completed }]
GET  /api/v1/grammar/lessons/{id}             -> + { explanation, examples: [{ zh, pinyin, en }] }
POST /api/v1/grammar/lessons/{id}/complete    -> { "xp_gained": 10, "total_xp": 10 }  // first time only
```

## HSK mock tests

```
POST /api/v1/tests/start?hsk_level=HSK1&num_questions=20      (1-60, default 20)
 -> { attempt_id, hsk_level, total_questions,
      questions: [{ id, question_type, question_text, option_a..option_d, audio_path }] }
    // correct answers are NOT included.

POST /api/v1/tests/{attempt_id}/submit
 body: { "answers": { "12": "B", "7": "A" } }     // question_id -> A|B|C|D; unanswered = wrong
 -> { attempt_id, total_questions, correct_answers, score_percent, passed, xp_gained,
      results: [{ question_id, chosen, correct, is_correct, explanation }] }
    // pass mark 60%. XP = 2/correct answer + 20 bonus if passed.
    // 409 if already submitted, 404 if the attempt belongs to another user.

GET  /api/v1/tests/history?limit=20   -> [{ id, hsk_level, score_percent, passed, finished_at }]
```

---

## Health Check
```
GET /health   (no auth)

→ 200  { "status": "ok", "version": "0.3.0" }
```

---

## Error format
All errors follow FastAPI default:
```json
{ "detail": "Human-readable message" }
```

HTTP codes used:
- `200` success
- `201` resource created
- `400` bad request / validation
- `401` invalid/missing token
- `404` not found
- `422` validation error (Pydantic)

---

## Frontend integration checklist (for Codex)

| Task | Detail |
|------|--------|
| Store tokens | `access_token` + `refresh_token` in SecureStore / AsyncStorage |
| Attach auth | `Authorization: Bearer <access_token>` on every request |
| Token refresh | On 401, call `/auth/refresh`, retry original request once |
| HSK levels | Enum values: `"HSK1"` … `"HSK6"` (string) |
| Definitions | Array of strings `["meaning1", "meaning2"]` |
| Pinyin | `pinyin` = tone-mark form `"nǐ hǎo"`, `pinyin_numeric` = `"ni3 hao3"` |
| Audio | See Audio section above |
| SRS card UX | Show word → user rates 0-5 → POST `/vocabulary/review` |
| XP display | From `GET /auth/me` `.xp` and `/vocabulary/progress` `.user_xp` |

---

## Running it

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend python scripts/import_hsk.py       # 5,375 words, safe to re-run; --prune also removes words no longer in the list (needed when migrating from the old list)
docker compose exec backend python scripts/import_content.py --prune   # reading, grammar, test questions
# Swagger UI: http://localhost:8000/docs
```
Tests (needs a Postgres): `cd backend && pip install -r requirements-dev.txt &&
TEST_DATABASE_URL=postgresql://user:pw@localhost:5432/test_db pytest` (DESTRUCTIVE: drops/recreates tables in that DB).

## Content status (be honest in the UI)

| Content | Have now | Note |
|---|---|---|
| Vocabulary | **5,375 words, current official HSK syllabus (2025-11, in force 2026-07), levels 1-6**: HSK1 300, HSK2 198, HSK3 497, HSK4 997, HSK5 1591, HSK6 1792 | Level = the level a word is *introduced* (not cumulative). Cumulative targets 300/500/1000/2000/3600/5400; 25 same-word-same-reading homograph rows are merged (so HSK2-6 are slightly under 200/500/1000/1600/1800). Levels 7-9 not included. **Replaces the earlier 2021-draft list (HSK1 was 510).** |
| Reading | 36 texts: 6 each for HSK1-6 | Every word validated at its level by `scripts/check_level.py` |
| Grammar | 48 lessons: 8 each for HSK1-6 | Aligned to the official grammar outline (each lesson has a `syllabus_ref`); all example sentences validated at their level |
| Test questions | **1,220: HSK1 220, HSK2-6 200 each** (generated from the word list: meaning, reverse, pinyin; HSK1 also has 20 hand-written) | no reading/listening/grammar-based questions yet |
| Audio | 83% of words have a human recording after `scripts/fetch_audio.py` (HSK1 93%, HSK6 76%) | no sentence/dialogue audio yet |

**Vocabulary notes for the UI**
- Words with several readings are separate rows: 行 `xíng` (HSK1, "to walk") and 行 `háng` (HSK3, "row"). Always show `pinyin` next to the hanzi.
- `pinyin` is syllable-spaced (`xiè xie`); `pinyin_numeric` too (`xie4 xie5`). `definitions` has 1-8 short English meanings.
- Page through lists (`limit` max 200 -> HSK6 is 9 pages). Default order: lowest HSK level first, then most frequent.
- The syllabus does include greetings such as 你好 and 谢谢 at HSK1.
- Local audio: `<hanzi>.mp3`, or `<hanzi>_<numeric pinyin without spaces>.mp3` (e.g. `行_xing2.mp3`) which wins for that reading.
- Source & licences (CC BY-SA attribution required): `backend/data/hsk/NOTICE.md`. Show an attribution line in the app's About screen.

## Known gaps (backend)
- `streak_days` now updates: it counts consecutive UTC days with any XP-earning activity (review, completed text/lesson, submitted test). Shown in `/auth/me` and `/vocabulary/progress`.
- Alembic migrations are set up (`backend/migrations/`). Fresh DB: `alembic upgrade head`; existing create_all DB: `alembic stamp head`. Startup also self-heals additive columns.
- Word `stroke_order_data` is empty (frontend can use the `hanzi-writer` package directly by character).

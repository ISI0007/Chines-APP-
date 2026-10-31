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
  "total": 150,
  "skip": 0,
  "limit": 50,
  "words": [
    {
      "id": 1,
      "simplified": "你好",
      "traditional": "你好",
      "pinyin": "nǐ hǎo",
      "pinyin_numeric": "ni3 hao3",
      "definitions": ["hello", "hi", "how are you"],
      "hsk_level": "HSK1",
      "frequency_rank": 1,
      "audio_path": "/api/v1/audio/hsk1/你好.mp3",   ← null if no file
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
    "HSK1": { "total": 150, "learned": 42, "due_for_review": 8 },
    "HSK2": { "total": 150, "learned": 0,  "due_for_review": 0 },
    ...
  }
}
```

---

## Audio

### Serve Local MP3
```
GET /api/v1/audio/{hsk_level}/{filename}
Example: GET /api/v1/audio/hsk1/你好.mp3

→ 200  audio/mpeg stream
→ 404  { "detail": "Audio file not found" }
```

**Frontend audio strategy:**
1. Check `word.audio_path` — if not null, fetch `GET /api/v1{audio_path}`
2. If null / 404, fall back to browser-side TTS:
   ```js
   `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(simplified)}&tl=zh-CN&client=tw-ob`
   ```
   Play with `expo-av` `Audio.Sound.createAsync({ uri })`.

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
    // correct answers are NOT included. 404 if no questions exist for that level.

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
docker compose exec backend python scripts/import_hsk.py       # 686 words, safe to re-run
docker compose exec backend python scripts/import_content.py   # reading, grammar, test questions
# Swagger UI: http://localhost:8000/docs
```
Tests (needs a Postgres): `cd backend && pip install -r requirements-dev.txt &&
TEST_DATABASE_URL=postgresql://user:pw@localhost:5432/test_db pytest` (DESTRUCTIVE: drops/recreates tables in that DB).

## Content status (be honest in the UI)

| Content | Have now | Note |
|---|---|---|
| Vocabulary | HSK1: 150, HSK2: 147, HSK3-6: 100 each (686 unique) | HSK3-6 are partial samples, NOT the full official lists |
| Reading | 5 HSK1 texts | |
| Grammar | 8 HSK1 lessons | |
| Test questions | 20 HSK1 | other levels return 404 from `/tests/start` |
| Audio files | none yet | `audio_path` is null -> use the TTS fallback above |

## Known gaps (backend)
- `streak_days` is never updated yet (needs a last-active column + migration).
- No Alembic migrations yet; `create_all` only creates missing tables.
- Word `stroke_order_data` is empty (frontend can use the `hanzi-writer` package directly by character).

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

## Health Check
```
GET /health   (no auth)

→ 200  { "status": "ok", "version": "0.2.0" }
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

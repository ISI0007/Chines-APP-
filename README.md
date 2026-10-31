# 学中文 — Chinese Learning App

A full-featured Chinese language learning platform inspired by Du Chinese, Hanzi, HSK apps, and Baobao.

## Features
- 📚 HSK 1–6 vocabulary with spaced repetition (SRS)
- 📖 Graded reading (pinyin toggle, tap-to-define)
- 🎧 Native audio listening exercises
- ✍️ Stroke order animation (hanzi-writer)
- 📝 HSK mock tests
- 🔥 Streaks, XP, progress tracking
- 🔐 JWT auth (register/login)

## Stack
| Layer | Tech |
|---|---|
| Backend | FastAPI + PostgreSQL + Redis |
| Frontend | React Native (Expo) |
| Auth | JWT (access + refresh) |
| SRS | SM-2 algorithm |
| Content | CC-CEDICT + open HSK lists |

## Quick Start

```bash
# 1. Clone the repo
git clone git@github.com:YOUR_USERNAME/chinese-learn.git
cd chinese-learn

# 2. Set up env
cp .env.example .env
# Edit .env with your values

# 3. Start services
docker compose up -d

# 4. Import HSK word data
docker compose exec backend python /scripts/import_hsk.py

# 5. API docs
open http://localhost:8000/docs

# 6. Frontend (separate terminal)
cd frontend
npm install
npx expo start
```

## Project Structure
```
chinese-learn/
├── backend/          # FastAPI API
│   ├── api/          # Routes
│   ├── core/         # Config, security
│   ├── db/           # Database engine
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── data/         # HSK lists, audio, CEDICT
├── frontend/         # React Native / Expo
│   ├── screens/      # App screens
│   ├── components/   # Reusable UI
│   ├── hooks/        # Zustand stores
│   └── constants/    # API URLs etc
├── scripts/          # Data import scripts
└── docker-compose.yml
```

## API Endpoints (Phase 1)
| Method | Path | Description |
|---|---|---|
| POST | /api/v1/auth/register | Create account |
| POST | /api/v1/auth/login | Login → tokens |
| POST | /api/v1/auth/refresh | Refresh access token |
| GET  | /api/v1/auth/me | Current user |
| GET  | /api/v1/vocabulary/words | List words (filter by HSK level) |
| GET  | /api/v1/vocabulary/words/{id} | Word detail |
| GET  | /health | Health check |

## Phases
- ✅ Phase 1 — Repo, backend, auth, DB schema, Docker
- 🔲 Phase 2 — Content pipeline (HSK lists, CC-CEDICT, audio)
- 🔲 Phase 3 — Flashcard UI + SRS
- 🔲 Phase 4 — Reading module
- 🔲 Phase 5 — Audio player + listening exercises
- 🔲 Phase 6 — HSK mock tests
- 🔲 Phase 7 — Progress dashboard
- 🔲 Phase 8 — Polish + Docker packaging

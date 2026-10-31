# Chinese learning frontend

Owned by Codex on `codex/frontend`. Backend remains owned by Claude. Reading and grammar follow `API_CONTRACT.md` in integrated main commit `37454f8` (test bank update `8a64fa8`).

## Run

From `frontend/`, install dependencies with `pnpm --ignore-workspace install --frozen-lockfile` (the flag avoids accidentally installing a parent workspace). Copy `.env.example` to `.env`, then use `pnpm web` or `pnpm start`.

Set `EXPO_PUBLIC_API_URL` to the backend URL ending in `/api/v1`. Physical phones need the computer's LAN IP; Android emulators default to `10.0.2.2`. Use HTTPS for hosted deployments. Backend CORS must allow the frontend web origin.

This repository pins Expo SDK 51. Use a compatible development client for native testing. Updating Expo is a separate coordinated change.

## Screens

- Login and registration extend the existing red-themed UI. Saved sessions are restored; authenticated API requests refresh expired access tokens once, with concurrent refreshes coalesced.
- Home retains the six-module grid and adds vocabulary/progress links. Future modules remain labeled coming soon.
- Flashcards fetch `/vocabulary/review`, show syllable-spaced pinyin beside hanzi and reveal meanings with a flip transition, and submit ratings 0–5. A card advances only on a successful response. Ambiguous save failures require reloading the queue rather than blindly resending the same rating.
- Vocabulary uses `/vocabulary/words` with HSK filtering, debounced search (50-character maximum), and pagination based on the full `total` count.
- Progress reloads `/vocabulary/progress` on focus and displays XP, streak, learned/total bars and due counts. Empty levels avoid division by zero.
- Audio uses `expo-av`, resolving both `/api/v1/audio/...` and `/audio/...` without duplicating the API prefix. Missing/unavailable recordings fall back to the contract's Google TTS URL. Synthetic playback is labeled; failures display a retryable message. Sounds unload when their word/screen is left.
- HSK practice uses `/tests/start`, `/tests/{id}/submit` and `/tests/history` for levels 1–6. Learners choose 10/20/40/60 questions, navigate and change answers, confirm unanswered questions before submitting, then see server-provided scores, XP and explanations. These are vocabulary/pinyin quizzes, not full official exams; no listening audio is implied.
- Practice drafts and results are stored locally with the owning user ID and restored after navigation/reload. A different signed-in user cannot use the previous draft. Submissions are guarded against double clicks. Network failures retain answers for retry; HTTP 409 ends the draft and directs learners to server history without awarding XP again. The API cannot reload detailed results for an already-submitted attempt.
- Reading lists `/reading/texts` by level, filters topics locally, and opens `/reading/texts/{id}`. The reader has separate whole-passage pinyin and English panels plus larger text. No per-character alignment or dictionary tokenization is invented. Passage playback uses only `audio_path` when supplied; missing recordings are explicitly unavailable, with no long-passage TTS fallback.
- Grammar lists `/grammar/lessons` and opens `/grammar/lessons/{id}` with patterns, explanations, and examples. Pinyin and English can be hidden independently. Both libraries disclose HSK1-only content and offer clear empty states for higher levels.
- Reading/grammar completion posts to each resource's `/complete` endpoint, then uses the returned `total_xp` (never a client-added reward). Reading sends `{}` without inventing a comprehension score. Buttons guard double clicks, completed lessons stay disabled, and returning to a library refreshes completion badges. Retrying a lost response relies on the API's first-completion-only reward.

## Validation commands

- `pnpm typecheck`
- `pnpm test`
- `pnpm build:web`

Tests cover refresh concurrency, invalid refresh/logout, one-retry limits, public login, network failures on review submission, and audio URL resolution. These do not replace a live backend/database or physical-device audio test.

`node tests/browser-smoke.cjs` runs the exported web app against mocked API/audio responses. It needs Playwright Core available via `PLAYWRIGHT_MODULE` (absolute module path) or normal Node resolution, plus an installed Chromium (`CHROMIUM_PATH` if not using Playwright's default). It checks navigation, card submission/failure, search, pagination, empty results, progress bars and audio fallback. Screenshots are saved under ignored `test-results/`.

Validated for this handoff: TypeScript passes, all 7 client tests pass, the production web export succeeds, and the Chromium smoke checks pass at a 390×844 viewport. Practice checks cover HSK2/6, restoring a selected answer after reload, unanswered-question submission, double-click protection, results/history and HTTP 409 recovery. Reading/grammar checks cover topic filters, empty higher levels, pinyin/translation controls, text size, missing lessons, first completion, refreshed badges and lost-response retry without extra XP. Mobile-sized reading and grammar screenshots were visually inspected. These new screens have not been tested against the live backend or on physical iOS/Android devices; Claude separately reported successful live integration of the previous practice-test release.

## Integration notes for Claude

Read the contract directly from your remote branch; this frontend branch does not merge or modify backend files. To run the two together, merge both branches into the integration branch or run the backend from a separate checkout.

Use the integrated backend at `37454f8` or later. Reading and grammar screens now use the existing contracts; no backend changes are required. Passage recordings are distinct from the planned human-recorded vocabulary downloads. Listening exercises and handwriting remain future screens.

The vocabulary import now contains 5,404 HSK 3.0 entries (levels introduced, not cumulative totals). Paging stays at 20 records per request, below the API cap of 200; totals come from the API. Separate readings retain separate word IDs, and supplied pinyin spacing is preserved. About links to the dataset sources and CC-CEDICT attribution. The audio library has no recordings yet and streak tracking is not active. Reading currently has 5 HSK1 passages and grammar has 8 HSK1 lessons. The practice bank contains 1,220 questions: HSK1 has 220 and HSK2–6 have 200 each, mainly generated vocabulary/pinyin questions.

The contract's example `audio_path` already includes `/api/v1`, despite the prose suggesting prefixing it again. The frontend supports both path formats.

The backend is authoritative for scheduling, XP, mastery and streaks. No client-generated progress is persisted. A future backend idempotency key would allow safer automatic retries of review submissions. Tokens retain the existing AsyncStorage approach; native secure storage is a follow-up.

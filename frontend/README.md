# Phase 3 frontend

Owned by Codex on `codex/frontend`. Backend remains owned by Claude. Implementation follows the updated `API_CONTRACT.md` from `origin/claude/backend` commit `86917df`.

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

## Validation commands

- `pnpm typecheck`
- `pnpm test`
- `pnpm build:web`

Tests cover refresh concurrency, invalid refresh/logout, one-retry limits, public login, network failures on review submission, and audio URL resolution. These do not replace a live backend/database or physical-device audio test.

`node tests/browser-smoke.cjs` runs the exported web app against mocked API/audio responses. It needs Playwright Core available via `PLAYWRIGHT_MODULE` (absolute module path) or normal Node resolution, plus an installed Chromium (`CHROMIUM_PATH` if not using Playwright's default). It checks navigation, card submission/failure, search, pagination, empty results, progress bars and audio fallback. Screenshots are saved under ignored `test-results/`.

Validated for this handoff: TypeScript passes, all 7 client tests pass, the production web export succeeds, and the Chromium smoke checks pass at a 390×844 viewport. The mobile-sized vocabulary screenshot was visually inspected. Live PostgreSQL/backend integration and physical iOS/Android playback have not been tested.

## Integration notes for Claude

Read the contract directly from your remote branch; this frontend branch does not merge or modify backend files. To run the two together, merge both branches into the integration branch or run the backend from a separate checkout.

Use backend commit `86917df` or later: it fixes the earlier first-review initialization failure. The updated reading, grammar and mock-test endpoints have been reviewed; their screens are outside this Phase 3 vocabulary/review/audio/progress task list.

The vocabulary import now contains 5,404 HSK 3.0 entries (levels introduced, not cumulative totals). Paging stays at 20 records per request, below the API cap of 200; totals come from the API. Separate readings retain separate word IDs, and supplied pinyin spacing is preserved. About links to the dataset sources and CC-CEDICT attribution. The audio library has no recordings yet and streak tracking is not active. Reading currently has 5 HSK1 passages, grammar has 8 HSK1 lessons, and mock tests have 20 HSK1 questions; do not advertise broader content when adding those screens.

The contract's example `audio_path` already includes `/api/v1`, despite the prose suggesting prefixing it again. The frontend supports both path formats.

The backend is authoritative for scheduling, XP, mastery and streaks. No client-generated progress is persisted. A future backend idempotency key would allow safer automatic retries of review submissions. Tokens retain the existing AsyncStorage approach; native secure storage is a follow-up.

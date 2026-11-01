/**
 * Chinese Learning App — canonical backend types (v0.3.0)
 * Auto-synced with backend schemas — DO NOT hand-edit.
 * Source of truth: openapi.json at repo root.
 *
 * Base URL : http://localhost:8000/api/v1
 * Auth     : Bearer <access_token>  (header: Authorization)
 * Refresh  : POST /auth/refresh  { refresh_token }  → Tokens
 */

// ─── Primitives ──────────────────────────────────────────────────────────────

export type HskLevel = "HSK1" | "HSK2" | "HSK3" | "HSK4" | "HSK5" | "HSK6";
export type Answer   = "A" | "B" | "C" | "D";

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface Tokens {
  access_token:  string;
  refresh_token: string;
  token_type:    string; // "bearer"
}

/** GET /auth/me  |  POST /auth/register */
export interface UserResponse {
  id:          number;
  email:       string;
  username:    string;
  hsk_level:   HskLevel;
  xp:          number;
  streak_days: number;
  is_active:   boolean;
}

// ─── Vocabulary ───────────────────────────────────────────────────────────────

export interface Word {
  id:                number;
  simplified:        string;
  traditional:       string | null;
  /** Tone-mark form, e.g. "nǐ hǎo" */
  pinyin:            string;
  /** Numeric form, e.g. "ni3 hao3" — may be null */
  pinyin_numeric:    string | null;
  definitions:       string[];
  hsk_level:         HskLevel;
  frequency_rank:    number | null;
  /** Full relative path e.g. "/api/v1/audio/hsk1/谢谢.mp3" — null → use TTS */
  audio_path:        string | null;
  stroke_order_data: string | null;
}

/** GET /vocabulary/words */
export interface WordPage {
  total: number;
  skip:  number;
  limit: number;
  words: Word[];
}

/** POST /vocabulary/review  —  body */
export interface ReviewRequest {
  word_id: number;
  /** SM-2 quality: 0=blackout … 5=perfect */
  quality: 0 | 1 | 2 | 3 | 4 | 5;
}

/** POST /vocabulary/review  —  response */
export interface ReviewResult {
  word_id:       number;
  next_review:   string;
  interval_days: number;
  ease_factor:   number;
  is_learned:    boolean;
  /** 5 if quality >= 3, else 1 */
  xp_gained:     number;
}

interface LevelProgress {
  total:          number;
  learned:        number;
  due_for_review: number;
}

/** GET /vocabulary/progress */
export interface VocabProgress {
  user_xp:     number;
  streak_days: number;
  /** Keys: "HSK1" ... "HSK6" */
  levels:      Record<HskLevel, LevelProgress>;
}

// ─── Reading ──────────────────────────────────────────────────────────────────

/** GET /reading/texts  — list item */
export interface ReadingSummary {
  id:           number;
  title:        string;
  title_pinyin: string;
  topic:        string;
  hsk_level:    HskLevel;
  word_count:   number;
  completed:    boolean;
}

/** GET /reading/texts/{id}  — full detail */
export interface ReadingDetail extends ReadingSummary {
  content:        string;
  content_pinyin: string;
  translation:    string;
  audio_path:     string | null;
}

/** POST /reading/texts/{id}/complete  — body */
export interface CompleteReadingRequest {
  comprehension_score?: number | null;
}

/** Generic XP response */
export interface XpResponse {
  xp_gained: number;
  total_xp:  number;
}

// ─── Grammar ──────────────────────────────────────────────────────────────────

export interface GrammarExample {
  zh:     string;
  pinyin: string;
  en:     string;
}

/** GET /grammar/lessons  — list item */
export interface GrammarSummary {
  id:          number;
  title:       string;
  hsk_level:   HskLevel;
  pattern:     string;
  order_index: number;
  completed:   boolean;
}

/** GET /grammar/lessons/{id}  — full detail */
export interface GrammarDetail extends GrammarSummary {
  explanation: string;
  examples:    GrammarExample[];
}

// ─── Tests ────────────────────────────────────────────────────────────────────

export interface TestQuestion {
  id:            number;
  question_type: string;
  question_text: string;
  option_a:      string;
  option_b:      string;
  option_c:      string;
  option_d:      string;
  audio_path:    string | null;
}

/** POST /tests/start  — response */
export interface TestStartResponse {
  attempt_id:      number;
  hsk_level:       HskLevel;
  total_questions: number;
  questions:       TestQuestion[];
}

/** POST /tests/{attempt_id}/submit  — body */
export interface TestSubmitRequest {
  /** Keys are question IDs as strings: { "12": "B" } */
  answers: Record<string, Answer>;
}

export interface QuestionResult {
  question_id: number;
  chosen:      Answer | null;
  correct:     Answer;
  is_correct:  boolean;
  explanation: string;
}

/** POST /tests/{attempt_id}/submit  — response */
export interface TestResult {
  attempt_id:      number;
  total_questions: number;
  correct_answers: number;
  score_percent:   number;
  passed:          boolean;
  xp_gained:       number;
  results:         QuestionResult[];
}

/** GET /tests/history  — list item */
export interface TestHistory {
  id:            number;
  hsk_level:     HskLevel;
  score_percent: number;
  passed:        boolean;
  finished_at:   string | null;
}

// ─── Writing ──────────────────────────────────────────────────────────────────

/** GET /writing/characters  — list item */
export interface WritingCharacter {
  id:              number;
  char:            string;
  pinyin:          string;
  meaning:         string[];
  hsk_level:       HskLevel;
  times_practiced: number;
  mastered:        boolean;
}

/** POST /writing/characters/{id}/practice  — body */
export interface PracticeRequest {
  mastered: boolean;
}

/** POST /writing/characters/{id}/practice  — response */
export interface PracticeResult {
  char_id:         number;
  times_practiced: number;
  mastered:        boolean;
  xp_gained:       number;
  total_xp:        number;
}

interface WritingLevelProgress {
  total:     number;
  practiced: number;
  mastered:  number;
}

/** GET /writing/progress */
export interface WritingProgress {
  levels: Record<HskLevel, WritingLevelProgress>;
}

// ─── Leaderboard ─────────────────────────────────────────────────────────────

/** One row in the leaderboard table */
export interface LeaderboardEntry {
  rank:        number;
  user_id:     number;
  username:    string;
  hsk_level:   HskLevel;
  xp:          number;
  streak_days: number;
}

/** GET /users/leaderboard */
export interface LeaderboardResponse {
  /** Top-N users by XP */
  top: LeaderboardEntry[];
  /** Current user's position if they are outside the top-N list; null otherwise */
  me:  LeaderboardEntry | null;
}

// ─── Health ───────────────────────────────────────────────────────────────────

/** GET /health  (no auth required) */
export interface HealthResponse {
  status:  string;
  version: string;
}

// ─── Backwards-compatible aliases (used by existing Codex screens) ────────────

/** @deprecated use VocabProgress */
export type Progress         = VocabProgress;
/** @deprecated use TestStartResponse */
export type TestAttempt      = TestStartResponse;
/** @deprecated use XpResponse */
export type CompletionResult = XpResponse;

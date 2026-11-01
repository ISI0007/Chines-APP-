// ─── Auth ────────────────────────────────────────────────────────────────────
export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string; // "bearer"
}

export interface User {
  id: number;
  email: string;
  username: string;
  hsk_level: HskLevel;
  xp: number;
  streak_days: number;
  is_active: boolean;
}

// ─── Vocabulary ──────────────────────────────────────────────────────────────
/** HSK level enum — matches backend HskLevel exactly. */
export type HskLevel = "HSK1" | "HSK2" | "HSK3" | "HSK4" | "HSK5" | "HSK6";

export interface Word {
  id: number;
  simplified: string;
  traditional: string;
  pinyin: string;
  /** Numeric-tone form, e.g. "ni3 hao3". */
  pinyin_numeric: string;
  definitions: string[];
  hsk_level: HskLevel;
  frequency_rank: number | null;
  /**
   * Full path to the local MP3, e.g. "/api/v1/audio/hsk1/谢谢.mp3".
   * null when no recording exists — fall back to TTS.
   */
  audio_path: string | null;
  stroke_order_data: string | null;
}

export interface WordPage {
  total: number;
  skip: number;
  limit: number;
  words: Word[];
}

export interface ReviewResult {
  word_id: number;
  next_review: string; // ISO-8601 UTC
  interval_days: number;
  ease_factor: number;
  is_learned: boolean;
  xp_gained: number;
}

export interface Progress {
  user_xp: number;
  streak_days: number;
  levels: Record<HskLevel, { total: number; learned: number; due_for_review: number }>;
}

// ─── Reading ─────────────────────────────────────────────────────────────────
export interface ReadingSummary {
  id: number;
  title: string;
  title_pinyin: string;
  topic: string;
  hsk_level: HskLevel;
  word_count: number;
  completed: boolean;
}

export interface ReadingDetail extends ReadingSummary {
  content: string;
  content_pinyin: string;
  translation: string;
  audio_path: string | null;
}

export interface XpResponse {
  xp_gained: number;
  total_xp: number;
}

// ─── Grammar ─────────────────────────────────────────────────────────────────
export interface GrammarExample {
  zh: string;
  pinyin: string;
  en: string;
}

export interface GrammarSummary {
  id: number;
  title: string;
  hsk_level: HskLevel;
  pattern: string;
  order_index: number;
  completed: boolean;
}

export interface GrammarDetail extends GrammarSummary {
  explanation: string;
  examples: GrammarExample[];
}

// ─── HSK mock tests ───────────────────────────────────────────────────────────
export type Answer = "A" | "B" | "C" | "D";

export interface TestQuestion {
  id: number;
  question_type: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  audio_path: string | null;
}

export interface TestAttempt {
  attempt_id: number;
  hsk_level: HskLevel;
  total_questions: number;
  questions: TestQuestion[];
}

export interface TestResult {
  attempt_id: number;
  total_questions: number;
  correct_answers: number;
  score_percent: number;
  passed: boolean;
  xp_gained: number;
  results: {
    question_id: number;
    chosen: Answer | null;
    correct: Answer;
    is_correct: boolean;
    explanation: string;
  }[];
}

export interface TestHistory {
  id: number;
  hsk_level: HskLevel;
  score_percent: number;
  passed: boolean;
  finished_at: string | null; // ISO-8601 or null
}

// ─── Writing (stroke order) ───────────────────────────────────────────────────
export interface Character {
  id: number;
  char: string;
  pinyin: string;
  meaning: string[];
  hsk_level: HskLevel;
  times_practiced: number;
  mastered: boolean;
}

export interface PracticeResult {
  char_id: number;
  times_practiced: number;
  mastered: boolean;
  xp_gained: number;
  total_xp: number;
}

export interface WritingProgress {
  levels: Record<HskLevel, { total: number; practiced: number; mastered: number }>;
}

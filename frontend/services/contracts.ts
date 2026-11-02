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
  id:             number;
  /** HSK 3.0: 'listening' | 'reading' | 'writing' */
  section:        string;
  question_number: number;
  question_type:  string;
  question_text:  string;
  option_a:       string;
  option_b:       string;
  option_c:       string;
  /** null for HSK1 3-choice questions */
  option_d:       string | null;
  audio_path:     string | null;
  /** HSK 3.0 picture-based writing tasks */
  image_url:      string | null;
  /** Groups questions belonging to the same reading passage */
  passage_id:     string | null;
  passage_text:   string | null;
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

// ─── Phase 3: Speaking / Shadowing ───────────────────────────────────────────

/** POST /shadowing/submit  —  request body */
export interface ShadowingSubmitRequest {
  /** Base64-encoded audio data */
  audio_base64:  string;
  /** "webm" | "wav" | "m4a" */
  audio_format:  "webm" | "wav" | "m4a";
  /** Chinese text user was reading, e.g. "你好" */
  target_text:   string;
  /** Pinyin of target_text, e.g. "nǐ hǎo" */
  target_pinyin: string;
}

export interface PhonemeScore {
  pinyin: string;
  /** 0.0 – 1.0 */
  score: number;
}

/** POST /shadowing/submit  —  response */
export interface ShadowingResult {
  /** Overall 0.0 – 1.0 */
  score: number;
  phoneme_breakdown: PhonemeScore[];
  feedback: string;
  /** "heuristic" when Whisper not configured; "whisper" when available */
  method: "heuristic" | "whisper";
}

// ─── Phase 3: Avatar ──────────────────────────────────────────────────────────

/** POST /users/me/avatar  —  response (multipart/form-data upload) */
export interface AvatarResponse {
  avatar_url: string;
}

// ─── Phase 3: Course levels / lessons ────────────────────────────────────────

/** One HSK level's summary — GET /course/levels */
export interface CourseLevelSummary {
  level:           HskLevel;
  lesson_count:    number;
  completed_count: number;
  completion_pct:  number;
}

/** GET /course/levels */
export interface CourseLevelsResponse {
  levels: CourseLevelSummary[];
}

/** One lesson row — GET /course/units?hsk_level=HSK1 */
export interface CourseLessonItem {
  id:            number;
  lesson_number: number;
  title_zh:      string;
  title_en:      string;
  topic:         string;
  has_audio:     boolean;
  completed:     boolean;
}

/** GET /course/units?hsk_level=HSK1 */
export interface CourseUnitsResponse {
  hsk_level: HskLevel;
  lessons:   CourseLessonItem[];
}

/** Audio track object inside a lesson detail */
export interface AudioTrack {
  section:    string;   // "new_words" | "dialogue_1" | "listening" | "exercise"
  track:      string;   // filename relative to audio_extracted/
  label:      string;
  duration_s: number;
}

/** GET /course/lessons/{id} */
export interface CourseLessonDetail {
  id:               number;
  hsk_level:        HskLevel;
  book:             "textbook" | "workbook";
  volume:           string;
  lesson_number:    number;
  title_zh:         string;
  title_en:         string;
  topic:            string;
  has_audio:        boolean;
  audio_tracks:     AudioTrack[];
  answer_key_pdf:   string | null;
  answer_key_pages: string;
}

/** POST /course/lessons/{id}/complete  —  response */
export interface LessonCompleteResult {
  lesson_id:         number;
  xp_earned:         number;
  total_xp:          number;
  streak_updated:    boolean;
  already_completed: boolean;
}

// ─── Phase 3: Listening tests ─────────────────────────────────────────────────

export interface ListeningQuestionOption {
  key:  string;   // "A" | "B" | "C" | "D"
  text: string;
}

/** One question in a listening test session */
export interface ListeningQuestion {
  id:                   string;
  audio_url:            string | null;
  question_text:        string;
  question_text_pinyin: string;
  options:              ListeningQuestionOption[];
}

/** GET /listening-test/{hsk_level}  —  response */
export interface ListeningTestSession {
  test_id:   number;
  hsk_level: HskLevel;
  questions: ListeningQuestion[];
}

/** One answer entry in POST /listening-test/{test_id}/submit */
export interface ListeningAnswerSubmit {
  question_id:     string;
  selected_option: string;   // "A" | "B" | "C" | "D"
}

/** POST /listening-test/{test_id}/submit  —  request body */
export interface ListeningSubmitRequest {
  answers: ListeningAnswerSubmit[];
}

export interface ListeningQuestionResult {
  question_id:    string;
  selected:       string | null;
  correct_option: string;
  is_correct:     boolean;
  explanation:    string;
}

/** POST /listening-test/{test_id}/submit  —  response */
export interface ListeningTestResult {
  test_id:         number;
  total_questions: number;
  correct_answers: number;
  score_percent:   number;
  passed:          boolean;
  xp_gained:       number;
  results:         ListeningQuestionResult[];
}

/** GET /listening-test/history  —  one row */
export interface ListeningTestHistoryItem {
  id:            number;
  hsk_level:     HskLevel;
  score_percent: number | null;
  passed:        boolean | null;
  started_at:    string;
  finished_at:   string | null;
}

// ─── Phase 3: HSK 3.0 Nine-Band Progression ──────────────────────────────────

export type BandStatus = "locked" | "in_progress" | "completed";

export interface HskBand {
  band:           number;   // 1 – 9
  status:         BandStatus;
  words_mastered: number;
  words_total:    number;
  pct:            number;   // 0.0 – 100.0
}

/** GET /progression */
export interface ProgressionResponse {
  current_band: number;
  bands:        HskBand[];
}

// ─── Phase 3: Profile ─────────────────────────────────────────────────────────

/** GET /users/me/profile */
export interface ProfileResponse {
  id:          number;
  username:    string;
  email:       string;
  hsk_level:   HskLevel;
  xp:          number;
  streak_days: number;
  avatar_url:  string | null;
}

// ─── Phase 3: Stroke-Order Scoring ───────────────────────────────────────────

/** POST /writing/characters/{char}/score  —  request body */
export interface StrokeScoreRequest {
  char:                   string;
  stroke_sequence:        [number, number][];   // [[x,y], …] per stroke
  expected_stroke_count?: number;
}

/** POST /writing/characters/{char}/score  —  response */
export interface StrokeScoreResponse {
  char:             string;
  score:            number;    // 0.0 – 1.0
  strokes_drawn:    number;
  strokes_expected: number;
  feedback:         string;
  xp_gained:        number;
  total_xp:         number;
}

// ─── Phase 3: Native Audio Mapping ───────────────────────────────────────────

/** GET|POST|DELETE /audio-admin/words/{word_id}/audio */
export interface AudioMappingResponse {
  word_id:    number;
  simplified: string;
  audio_path: string | null;
  audio_url:  string | null;
}

// ─── Backwards-compatible aliases (used by existing Codex screens) ────────────

/** @deprecated use VocabProgress */
export type Progress         = VocabProgress;
/** @deprecated use TestStartResponse */
export type TestAttempt      = TestStartResponse;
/** @deprecated use XpResponse */
export type CompletionResult = XpResponse;

export interface Word { id: number; simplified: string; traditional: string; pinyin: string; definitions: string[]; hsk_level: string; audio_path: string | null }
export interface WordPage { total: number; skip: number; limit: number; words: Word[] }
export interface ReviewResult { word_id: number; next_review: string; interval_days: number; xp_gained: number }
export interface Progress { user_xp: number; streak_days: number; levels: Record<string, { total: number; learned: number; due_for_review: number }> }
export interface Tokens { access_token: string; refresh_token: string }
export type Answer = "A" | "B" | "C" | "D";
export interface TestQuestion {
  id: number; question_type: string; question_text: string;
  option_a: string; option_b: string; option_c: string; option_d: string;
  audio_path: string | null;
}
export interface TestAttempt { attempt_id: number; hsk_level: string; total_questions: number; questions: TestQuestion[] }
export interface TestResult {
  attempt_id: number; total_questions: number; correct_answers: number; score_percent: number;
  passed: boolean; xp_gained: number;
  results: { question_id: number; chosen: Answer | null; correct: Answer; is_correct: boolean; explanation: string }[];
}
export interface TestHistory { id: number; hsk_level: string; score_percent: number; passed: boolean; finished_at: string | null }

export interface Word { id: number; simplified: string; traditional: string; pinyin: string; definitions: string[]; hsk_level: string; audio_path: string | null }
export interface WordPage { total: number; skip: number; limit: number; words: Word[] }
export interface ReviewResult { word_id: number; next_review: string; interval_days: number; xp_gained: number }
export interface Progress { user_xp: number; streak_days: number; levels: Record<string, { total: number; learned: number; due_for_review: number }> }
export interface Tokens { access_token: string; refresh_token: string }

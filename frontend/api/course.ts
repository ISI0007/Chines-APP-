import { API_BASE } from "../constants/api";
import { api } from "../hooks/useAuth";

export type CourseLevel = "HSK1" | "HSK2" | "HSK3" | "HSK4";
export type CourseSection = "new_words" | "text_1" | "extension" | "text_2" | "listening_1" | "listening_2" | "listening_3" | "hsk_practice";
export interface LessonSummary { id: number; lesson_number: number; title_zh: string; title_en: string; topic: string; track_count: number; answer_key_pdf?: string | null }
export interface AudioTrack { section: CourseSection; label_zh: string; label: string; track: string; duration_s: number }
export interface LessonDetail extends LessonSummary { audio_tracks: AudioTrack[] }

export const getLessons = (hskLevel: CourseLevel, volume?: "A" | "B", signal?: AbortSignal) => {
  const params = new URLSearchParams({ hsk_level: hskLevel });
  if (volume) params.set("volume", volume);
  return api<LessonSummary[]>(`/course/lessons?${params}`, { signal });
};
export const getLesson = (id: number, signal?: AbortSignal) => api<LessonDetail>(`/course/lessons/${id}`, { signal });

export function audioUrl(trackPath: string): string {
  const base = new URL(API_BASE);
  const path = trackPath.replace(/^\/+/, "").split("/").map(part => encodeURIComponent(decodeURIComponent(part))).join("/");
  return new URL(path.startsWith("api/") ? `/${path}` : `/api/v1/course/audio/${path}`, base.origin).toString();
}

export function answerKeyUrl(filename: string): string {
  const base = new URL(API_BASE);
  return new URL(`/api/v1/course/answer-key/${filename.split("/").map(part => encodeURIComponent(decodeURIComponent(part))).join("/")}`, base.origin).toString();
}

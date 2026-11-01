import { api } from "../hooks/useAuth";
import type { Flashcard, FlashcardReview, Book, BookDetail, MockTest, MockResult, Phase2Progress, WritingCharacter, WritingPractice } from "./contracts";
export type { Flashcard, Book, BookDetail, MockTest, MockResult, Phase2Progress } from "./contracts";

// Phase 2 contract. Keep endpoint shapes here so Claude's OpenAPI export can be
// reconciled in one place when it arrives.

export const phase2 = {
  flashcards: async (level: string, signal?: AbortSignal) => (await api<Flashcard[]>(`/flashcards/hsk/${encodeURIComponent(level)}`, { signal })).map(word => ({ ...word, meaning: word.meaning || word.definitions?.join("; ") || "" })),
  review: (word_id: number, quality: number) => api<FlashcardReview>("/flashcards/review", { method: "POST", body: JSON.stringify({ word_id, quality }) }),
  books: (signal?: AbortSignal) => api<Book[]>("/reader/books", { signal }),
  book: (id: number, signal?: AbortSignal) => api<BookDetail>(`/reader/books/${id}`, { signal }),
  mockTest: (level: string) => api<MockTest>(`/mock-test/hsk/${encodeURIComponent(level)}`),
  submitMock: (test_id: number, answers: Record<number, number>) => api<MockResult>("/mock-test/submit", { method: "POST", body: JSON.stringify({ test_id, answers }) }),
  progress: (signal?: AbortSignal) => api<Phase2Progress>("/progress/me", { signal }),
};
export const FlashcardAPI = { list: phase2.flashcards, review: phase2.review };
export const ReaderAPI = { books: phase2.books, book: phase2.book };
export const MockTestAPI = { start: phase2.mockTest, submit: phase2.submitMock };
export const ProgressAPI = { me: phase2.progress };
export const WritingAPI = {
  characters: (level: string, signal?: AbortSignal) => api<WritingCharacter[]>(`/writing/characters?hsk_level=${encodeURIComponent(level)}`, { signal }),
  practice: (char_id: number, mastered: boolean) => api<WritingPractice>(`/writing/characters/${char_id}/practice`, { method: "POST", body: JSON.stringify({ mastered }) }),
};

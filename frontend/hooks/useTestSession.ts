import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";
import type { Answer, TestAttempt, TestResult } from "../services/contracts";

interface TestSession {
  ownerId: number | null;
  attempt: TestAttempt | null;
  answers: Record<number, Answer>;
  index: number;
  result: TestResult | null;
  submitted: boolean;
}
export const emptyTestSession: TestSession = { ownerId: null, attempt: null, answers: {}, index: 0, result: null, submitted: false };
// A draft survives navigation/reloads. The screen only reads a draft owned by the signed-in user.
export const useTestSession = create(persist<TestSession>(() => ({ ...emptyTestSession }), {
  name: "hsk-test-session-v1",
  storage: createJSONStorage(() => AsyncStorage),
  skipHydration: true,
}));

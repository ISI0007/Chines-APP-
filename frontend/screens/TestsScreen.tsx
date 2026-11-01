import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Button,
  Pressable,
  ScrollView,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api, useAuth } from "../hooks/useAuth";
import { emptyTestSession, useTestSession } from "../hooks/useTestSession";
import { Failure, Levels, ui } from "../components/StudyUI";
import { ApiError } from "../services/client";
import type {
  Answer,
  TestAttempt,
  TestHistory,
  TestResult,
} from "../services/contracts";

const CHOICES: Answer[] = ["A", "B", "C", "D"];

// ── HSK 3.0 section metadata ─────────────────────────────────────────────────
const SECTION_LABELS: Record<string, string> = {
  listening: "🎧 Listening",
  reading:   "📖 Reading",
  writing:   "✏️  Writing",
};
const SECTION_ORDER = ["listening", "reading", "writing"];

type TestMode = "practice" | "full";

// ── section tabs ──────────────────────────────────────────────────────────────
function SectionTabs({
  sections,
  active,
  onChange,
  disabled,
}: {
  sections: string[];
  active: string | null;
  onChange: (s: string | null) => void;
  disabled: boolean;
}) {
  return (
    <View style={[ui.row, { flexWrap: "wrap", gap: 6 }]}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="All sections"
        accessibilityState={{ selected: active === null }}
        disabled={disabled}
        style={[ui.chip, active === null && ui.selected]}
        onPress={() => onChange(null)}
      >
        <Text>All</Text>
      </Pressable>
      {SECTION_ORDER.filter(s => sections.includes(s)).map(s => (
        <Pressable
          key={s}
          accessibilityRole="button"
          accessibilityLabel={SECTION_LABELS[s] ?? s}
          accessibilityState={{ selected: active === s }}
          disabled={disabled}
          style={[ui.chip, active === s && ui.selected]}
          onPress={() => onChange(s)}
        >
          <Text>{SECTION_LABELS[s] ?? s}</Text>
        </Pressable>
      ))}
    </View>
  );
}

// ── section badge shown inline during test ────────────────────────────────────
function SectionBadge({ section }: { section?: string }) {
  if (!section) return null;
  return (
    <View
      style={{
        alignSelf: "flex-start",
        backgroundColor: "#a63232",
        borderRadius: 4,
        paddingHorizontal: 8,
        paddingVertical: 2,
        marginBottom: 6,
      }}
    >
      <Text style={{ color: "#fff", fontSize: 12, fontWeight: "600" }}>
        {SECTION_LABELS[section] ?? section}
      </Text>
    </View>
  );
}

// ── passage block (shared reading passages) ───────────────────────────────────
function PassageBlock({ text }: { text: string }) {
  return (
    <View
      style={{
        backgroundColor: "#f5f0eb",
        borderLeftWidth: 3,
        borderLeftColor: "#a63232",
        borderRadius: 4,
        padding: 10,
        marginBottom: 8,
      }}
    >
      <Text style={{ fontSize: 13, color: "#555", fontStyle: "italic" }}>
        Read the passage:
      </Text>
      <Text style={{ fontSize: 15, lineHeight: 22, marginTop: 4 }}>{text}</Text>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
export default function TestsScreen() {
  const userId    = useAuth(state => state.user?.id ?? null);
  const session   = useTestSession();

  const [ready, setReady]               = useState(false);
  const [level, setLevel]               = useState("HSK1");
  const [count, setCount]               = useState(20);
  const [mode, setMode]                 = useState<TestMode>("practice");
  const [section, setSection]           = useState<string | null>(null);
  const [availSections, setAvailSects]  = useState<string[]>([]);
  const [sectionsLoading, setSectLoad]  = useState(false);

  const [busy, setBusy]                 = useState(false);
  const [error, setError]               = useState("");
  const [confirm, setConfirm]           = useState(false);
  const [history, setHistory]           = useState<TestHistory[]>([]);
  const [historyBusy, setHistoryBusy]   = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyRefresh, setHistRefresh]= useState(0);

  const pending = useRef(false);

  // ── restore persisted session ──────────────────────────────────────────────
  useEffect(() => {
    let active = true;
    Promise.resolve(useTestSession.persist.rehydrate()).finally(() => {
      if (!active) return;
      if (useTestSession.getState().ownerId !== userId)
        useTestSession.setState({ ...emptyTestSession, ownerId: userId });
      setReady(true);
    });
    return () => { active = false; };
  }, [userId]);

  // ── load available sections when level changes ─────────────────────────────
  useEffect(() => {
    setSectLoad(true);
    setSection(null);
    api<string[]>(`/tests/sections?hsk_level=${level}`)
      .then(data => setAvailSects(data))
      .catch(() => setAvailSects(["reading"])) // graceful fallback
      .finally(() => setSectLoad(false));
  }, [level]);

  // ── history ────────────────────────────────────────────────────────────────
  useFocusEffect(
    useCallback(() => {
      const controller = new AbortController();
      setHistoryBusy(true);
      setHistoryError("");
      api<TestHistory[]>("/tests/history?limit=20", { signal: controller.signal })
        .then(data => { if (!controller.signal.aborted) setHistory(data); })
        .catch(() => {
          if (!controller.signal.aborted)
            setHistoryError("Could not load previous attempts.");
        })
        .finally(() => {
          if (!controller.signal.aborted) setHistoryBusy(false);
        });
      return () => controller.abort();
    }, [historyRefresh]),
  );

  const owned    = session.ownerId === userId;
  const attempt  = owned ? session.attempt : null;
  const result   = owned ? session.result  : null;
  const question = attempt?.questions[session.index];
  const answered = attempt?.questions.filter(q => session.answers[q.id]).length ?? 0;

  // ── current section being tested (for full-mode progress header) ───────────
  const currentSection = question?.section ?? null;
  const prevPassageId  = useRef<string | null>(null);
  const showPassage    =
    question?.passage_text && question?.passage_id !== prevPassageId.current;
  if (showPassage) prevPassageId.current = question?.passage_id ?? null;

  // ── start ──────────────────────────────────────────────────────────────────
  async function start() {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      const params = new URLSearchParams({
        hsk_level:     level,
        num_questions: String(count),
        mode,
      });
      if (mode === "practice" && section) params.set("section", section);

      const data = await api<TestAttempt>(
        `/tests/start?${params.toString()}`,
        { method: "POST" },
      );
      if (useAuth.getState().user?.id !== userId) return;
      if (!data.questions.length) throw new Error("No questions returned.");
      useTestSession.setState({ ...emptyTestSession, ownerId: userId, attempt: data });
      prevPassageId.current = null;
      setConfirm(false);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 404
          ? "No questions available for this level/section yet. Try another option."
          : "Could not start the test. Please try again.",
      );
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  // ── submit ─────────────────────────────────────────────────────────────────
  async function submit() {
    if (pending.current || !attempt || session.submitted) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      const data = await api<TestResult>(
        `/tests/${attempt.attempt_id}/submit`,
        { method: "POST", body: JSON.stringify({ answers: session.answers }) },
      );
      if (useAuth.getState().user?.id !== userId) return;
      useTestSession.setState({ result: data, submitted: true });
      const user = useAuth.getState().user;
      if (user)
        useAuth.setState({ user: { ...user, xp: user.xp + data.xp_gained } });
      setConfirm(false);
      setHistRefresh(n => n + 1);
    } catch (err) {
      if (useAuth.getState().user?.id !== userId) return;
      if (err instanceof ApiError && err.status === 409) {
        useTestSession.setState({ submitted: true });
        setConfirm(false);
        setHistRefresh(n => n + 1);
        setError(
          "This attempt was already submitted. Its score is in recent attempts.",
        );
      } else if (err instanceof ApiError && err.status === 404) {
        setError(
          "This attempt is no longer available. You can leave it and start a new test.",
        );
      } else {
        setError(
          "Submission could not be confirmed. Your answers are kept. Retry submission.",
        );
      }
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  function reset() {
    useTestSession.setState({ ...emptyTestSession, ownerId: userId });
    prevPassageId.current = null;
    setConfirm(false);
    setError("");
  }

  // ── render ─────────────────────────────────────────────────────────────────
  if (!ready) return <ActivityIndicator accessibilityLabel="Restoring practice test" />;

  return (
    <ScrollView contentContainerStyle={ui.page}>
      <Text style={ui.title}>HSK 3.0 Practice Tests</Text>
      <Text style={ui.subtitle}>
        Section-based practice (Listening · Reading · Writing) for HSK 1–6.
        Full-exam mode delivers questions in official section order.
      </Text>

      {!!error && <Text accessibilityRole="alert">{error}</Text>}

      {/* ── SETUP SCREEN ── */}
      {!attempt ? (
        <>
          <Levels value={level} onChange={setLevel} disabled={busy} />

          {/* ── Mode selector ── */}
          <Text style={{ fontWeight: "600", marginTop: 12 }}>Test mode</Text>
          <View style={[ui.row, { gap: 8 }]}>
            {(["practice", "full"] as TestMode[]).map(m => (
              <Pressable
                key={m}
                accessibilityRole="button"
                accessibilityLabel={m === "full" ? "Full exam mode" : "Practice mode"}
                accessibilityState={{ selected: mode === m }}
                disabled={busy}
                style={[ui.chip, mode === m && ui.selected]}
                onPress={() => setMode(m)}
              >
                <Text>{m === "full" ? "📋 Full exam" : "🎯 Practice"}</Text>
              </Pressable>
            ))}
          </View>

          {/* ── Section filter (practice only) ── */}
          {mode === "practice" && (
            <>
              <Text style={{ fontWeight: "600", marginTop: 12 }}>Section</Text>
              {sectionsLoading ? (
                <ActivityIndicator accessibilityLabel="Loading sections" />
              ) : (
                <SectionTabs
                  sections={availSections}
                  active={section}
                  onChange={setSection}
                  disabled={busy}
                />
              )}
            </>
          )}

          {/* ── Question count (practice only) ── */}
          {mode === "practice" && (
            <>
              <Text style={{ fontWeight: "600", marginTop: 12 }}>
                Questions per session
              </Text>
              <View style={ui.row}>
                {[10, 20, 40, 60].map(n => (
                  <Pressable
                    key={n}
                    accessibilityRole="button"
                    accessibilityLabel={`${n} questions`}
                    accessibilityState={{ selected: count === n }}
                    disabled={busy}
                    style={[ui.chip, count === n && ui.selected]}
                    onPress={() => setCount(n)}
                  >
                    <Text>{n}</Text>
                  </Pressable>
                ))}
              </View>
            </>
          )}

          {mode === "full" && (
            <Text style={{ color: "#888", fontSize: 12, marginTop: 8 }}>
              Full exam delivers all available questions in official section
              order: Listening → Reading → Writing.
            </Text>
          )}

          <Button
            title={busy ? "Starting…" : mode === "full" ? "Start full exam" : "Start practice"}
            onPress={start}
            disabled={busy || sectionsLoading}
            color="#a63232"
          />
        </>
      ) : result ? (
        /* ── RESULTS SCREEN ── */
        <>
          <View style={ui.card}>
            <Text style={ui.title}>
              {result.score_percent}% ·{" "}
              {result.passed ? "✅ Passed" : "📚 Keep practising"}
            </Text>
            <Text>
              {result.correct_answers} / {result.total_questions} correct ·
              +{result.xp_gained} XP
            </Text>
            <Text>Practice pass mark: 60%</Text>
          </View>

          <Button title="Start another practice" onPress={reset} />

          <Text style={ui.pinyin}>Review your answers</Text>
          {result.results.map(item => {
            const q = attempt.questions.find(q => q.id === item.question_id);
            const opt = (choice: Answer) =>
              q?.[`option_${choice.toLowerCase()}` as "option_a"] ?? "";
            return (
              <View key={item.question_id} style={ui.card}>
                {q?.section && <SectionBadge section={q.section} />}
                <Text>{q?.question_text ?? `Question ${item.question_id}`}</Text>
                <Text>
                  {item.is_correct ? "✅ Correct" : "❌ Incorrect"} · Your
                  answer:{" "}
                  {item.chosen
                    ? `${item.chosen} · ${opt(item.chosen as Answer)}`
                    : "Unanswered"}
                </Text>
                <Text>
                  Correct: {item.correct} · {opt(item.correct as Answer)}
                </Text>
                {!!item.explanation && <Text>{item.explanation}</Text>}
              </View>
            );
          })}
        </>
      ) : session.submitted ? (
        <View style={ui.card}>
          <Text>This attempt was submitted. See its score in recent attempts.</Text>
          <Button title="Start another practice" onPress={reset} />
        </View>
      ) : question ? (
        /* ── QUESTION SCREEN ── */
        <>
          {/* Progress header */}
          <Text>
            {attempt.hsk_level} · Question {session.index + 1} of{" "}
            {attempt.total_questions} · {answered} answered
          </Text>

          {/* Section badge */}
          {currentSection && <SectionBadge section={currentSection} />}

          {/* Shared passage (shown once per passage_id) */}
          {question.passage_text && (
            <PassageBlock text={question.passage_text} />
          )}

          {/* Audio hint for listening */}
          {question.section === "listening" && (
            <View
              style={{
                backgroundColor: "#fff8f0",
                borderRadius: 6,
                padding: 8,
                marginBottom: 6,
              }}
            >
              <Text style={{ color: "#a63232", fontSize: 13 }}>
                🎧 Listening question — read the dialogue or monologue carefully.
              </Text>
            </View>
          )}

          <View style={ui.card}>
            <Text style={ui.pinyin}>{question.question_text}</Text>
            {CHOICES.filter(c => c !== "D" || question.option_d).map(choice => (
              <Pressable
                key={choice}
                accessibilityRole="radio"
                aria-checked={session.answers[question.id] === choice}
                aria-disabled={busy}
                disabled={busy}
                style={[
                  ui.chip,
                  session.answers[question.id] === choice && ui.selected,
                ]}
                onPress={() => {
                  useTestSession.setState({
                    answers: { ...session.answers, [question.id]: choice },
                  });
                  setConfirm(false);
                }}
              >
                <Text>
                  {choice} ·{" "}
                  {question[`option_${choice.toLowerCase()}` as "option_a"] ?? ""}
                </Text>
              </Pressable>
            ))}
          </View>

          {/* Prev / Next navigation */}
          <View style={ui.row}>
            <Button
              title="◀ Prev"
              disabled={busy || session.index === 0}
              onPress={() => {
                useTestSession.setState({ index: session.index - 1 });
                setConfirm(false);
              }}
            />
            <Button
              title="Next ▶"
              disabled={busy || session.index >= attempt.questions.length - 1}
              onPress={() => {
                useTestSession.setState({ index: session.index + 1 });
                setConfirm(false);
              }}
            />
          </View>

          {/* Jump to question by section (full-exam mode convenience) */}
          {attempt.questions.some(q => q.section !== attempt.questions[0].section) && (
            <View style={[ui.row, { flexWrap: "wrap", gap: 4, marginTop: 4 }]}>
              {SECTION_ORDER.filter(s =>
                attempt.questions.some(q => q.section === s),
              ).map(s => {
                const firstIdx = attempt.questions.findIndex(q => q.section === s);
                return (
                  <Pressable
                    key={s}
                    style={[ui.chip, currentSection === s && ui.selected]}
                    onPress={() =>
                      useTestSession.setState({ index: firstIdx })
                    }
                  >
                    <Text style={{ fontSize: 12 }}>
                      {SECTION_LABELS[s] ?? s}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          )}

          {/* Submit flow */}
          {confirm ? (
            <View style={ui.card}>
              <Text>
                {attempt.total_questions - answered} unanswered. Unanswered
                count as incorrect. Submit this attempt?
              </Text>
              <Button
                title={busy ? "Submitting…" : "Confirm submission"}
                disabled={busy}
                onPress={submit}
                color="#a63232"
              />
              <Button
                title="Keep answering"
                disabled={busy}
                onPress={() => setConfirm(false)}
              />
            </View>
          ) : (
            <Button
              title="Finish practice"
              disabled={busy}
              onPress={() => setConfirm(true)}
              color="#a63232"
            />
          )}

          <Text>Your draft is saved on this device. Return here to continue.</Text>
          {!!error && (
            <Button title="Leave this attempt" disabled={busy} onPress={reset} />
          )}
        </>
      ) : null}

      {/* ── HISTORY ── */}
      <Text style={[ui.pinyin, { marginTop: 24 }]}>Recent attempts</Text>
      {historyBusy ? (
        <ActivityIndicator accessibilityLabel="Loading attempt history" />
      ) : historyError ? (
        <Failure
          message={historyError}
          retry={() => setHistRefresh(n => n + 1)}
        />
      ) : history.length === 0 ? (
        <Text>No completed attempts yet.</Text>
      ) : (
        history.map(item => (
          <View key={item.id} style={ui.card}>
            <Text>
              Attempt #{item.id} · {item.hsk_level} · {item.score_percent}%{" "}
              · {item.passed ? "Passed ✅" : "Keep practising 📚"}
            </Text>
            <Text>
              {item.finished_at
                ? new Date(item.finished_at).toLocaleString()
                : ""}
            </Text>
          </View>
        ))
      )}
      <Button
        title="Refresh history"
        disabled={historyBusy}
        onPress={() => setHistRefresh(n => n + 1)}
      />
    </ScrollView>
  );
}

import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api, useAuth } from "../hooks/useAuth";
import { Failure, Levels, ui } from "../components/StudyUI";
import type {
  ListeningAnswerSubmit,
  ListeningQuestion,
  ListeningSubmitRequest,
  ListeningTestResult,
  ListeningTestSession,
} from "../services/contracts";

type Phase = "select" | "testing" | "result";

function QuestionCard({
  q,
  selected,
  onSelect,
  disabled,
}: {
  q: ListeningQuestion;
  selected: string | null;
  onSelect(opt: string): void;
  disabled: boolean;
}) {
  return (
    <View style={s.qCard}>
      <Text style={s.qText}>{q.question_text}</Text>
      {q.options.map(opt => (
        <TouchableOpacity
          key={opt.key}
          style={[s.option, selected === opt.key && s.optionSelected]}
          onPress={() => onSelect(opt.key)}
          disabled={disabled}
          accessibilityRole="radio"
          accessibilityState={{ selected: selected === opt.key, disabled }}
        >
          <Text style={[s.optionKey, selected === opt.key && s.optionKeySelected]}>{opt.key}</Text>
          <Text style={[s.optionText, selected === opt.key && s.optionTextSelected]}>{opt.text}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

export default function ListeningTestScreen() {
  const { user } = useAuth();
  const [level, setLevel] = useState("HSK1");
  const [phase, setPhase] = useState<Phase>("select");
  const [session, setSession] = useState<ListeningTestSession | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ListeningTestResult | null>(null);
  const [error, setError] = useState("");

  function reset() {
    setPhase("select");
    setSession(null);
    setAnswers({});
    setResult(null);
    setError("");
  }

  async function startTest() {
    setBusy(true); setError("");
    try {
      const s = await api<ListeningTestSession>(`/listening-test/${level}`);
      setSession(s);
      setAnswers({});
      setPhase("testing");
    } catch (e: any) {
      setError(e?.message ?? "Could not load test.");
    } finally {
      setBusy(false);
    }
  }

  async function submitTest() {
    if (!session) return;
    const unanswered = session.questions.filter(q => !answers[q.id]);
    if (unanswered.length > 0) {
      setError(`Please answer all questions (${unanswered.length} remaining).`);
      return;
    }
    setSubmitting(true); setError("");
    try {
      const answerList: ListeningAnswerSubmit[] = Object.entries(answers).map(
        ([question_id, selected_option]) => ({ question_id, selected_option }),
      );
      const body: ListeningSubmitRequest = { answers: answerList };
      const r = await api<ListeningTestResult>(
        `/listening-test/${session.test_id}/submit`,
        { method: "POST", body: JSON.stringify(body) },
      );
      setResult(r);
      setPhase("result");
      if (user) {
        useAuth.setState({ user: { ...user, xp: user.xp + r.xp_gained } });
      }
    } catch (e: any) {
      setError(e?.message ?? "Submission failed.");
    } finally {
      setSubmitting(false);
    }
  }

  // — Select phase —
  if (phase === "select") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={ui.page}>
        <Text style={ui.title}>🎧 Listening Test</Text>
        <Text style={ui.subtitle}>Test your HSK listening comprehension.</Text>
        <Levels value={level} onChange={setLevel} disabled={busy} />
        {!!error && <Failure message={error} retry={() => setError("")} />}
        <TouchableOpacity style={s.startBtn} onPress={startTest} disabled={busy}>
          {busy ? <ActivityIndicator color="#fff" /> : <Text style={s.startBtnText}>▶ Start {level} test</Text>}
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // — Testing phase —
  if (phase === "testing" && session) {
    const answered = Object.keys(answers).length;
    return (
      <ScrollView style={styles.container} contentContainerStyle={ui.page}>
        <View style={s.testHeader}>
          <Text style={s.testTitle}>{level} Listening</Text>
          <Text style={s.testProgress}>{answered}/{session.questions.length} answered</Text>
        </View>

        {session.questions.map((q, i) => (
          <View key={q.id}>
            <Text style={s.qNum}>Question {i + 1}</Text>
            <QuestionCard
              q={q}
              selected={answers[q.id] ?? null}
              onSelect={opt => setAnswers(a => ({ ...a, [q.id]: opt }))}
              disabled={submitting}
            />
          </View>
        ))}

        {!!error && <Failure message={error} retry={() => setError("")} />}

        <View style={ui.row}>
          <TouchableOpacity style={s.cancelBtn} onPress={reset} disabled={submitting}>
            <Text style={s.cancelText}>✕ Cancel</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[s.submitBtn, answered < session.questions.length && s.submitBtnDisabled]}
            onPress={submitTest} disabled={submitting}>
            {submitting
              ? <ActivityIndicator color="#fff" />
              : <Text style={s.submitBtnText}>Submit →</Text>
            }
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  // — Result phase —
  if (phase === "result" && result) {
    const pct = Math.round(result.score_percent);
    const color = result.passed ? "#3a9e6b" : "#b73535";
    return (
      <ScrollView style={styles.container} contentContainerStyle={ui.page}>
        <Text style={ui.title}>{result.passed ? "🎉 Passed!" : "😅 Try again"}</Text>

        <View style={[ui.card, s.scoreCard]}>
          <Text style={[s.bigScore, { color }]}>{pct}%</Text>
          <Text style={s.scoreLabel}>{result.passed ? "Pass" : "Fail"} · 60% required</Text>
          <Text style={s.xpEarned}>+{result.xp_gained} XP earned</Text>
        </View>

        {/* Per-question breakdown */}
        <Text style={s.sectionTitle}>Question breakdown</Text>
        {result.question_results.map((qr, i) => (
          <View key={qr.question_id} style={[s.qResult, qr.correct ? s.qResultPass : s.qResultFail]}>
            <View style={s.qResultHeader}>
              <Text style={s.qResultNum}>Q{i + 1}</Text>
              <Text style={qr.correct ? s.correct : s.wrong}>
                {qr.correct ? "✓ Correct" : "✗ Wrong"}
              </Text>
            </View>
            <Text style={s.qResultMeta}>
              Your answer: <Text style={{ fontWeight: "600" }}>{qr.selected_option}</Text>
              {"  ·  "}Correct: <Text style={{ fontWeight: "600", color: "#3a9e6b" }}>{qr.correct_option}</Text>
            </Text>
            {qr.explanation ? <Text style={s.explanation}>{qr.explanation}</Text> : null}
          </View>
        ))}

        <View style={ui.row}>
          <TouchableOpacity style={s.cancelBtn} onPress={reset}>
            <Text style={s.cancelText}>← Back</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.submitBtn} onPress={() => { reset(); setTimeout(startTest, 50); }}>
            <Text style={s.submitBtnText}>Retry →</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return null;
}

const styles = StyleSheet.create({ container: { flex: 1, backgroundColor: "#faf8f4" } });
const s = StyleSheet.create({
  startBtn: { backgroundColor: "#b73535", borderRadius: 16, padding: 18, alignItems: "center" },
  startBtnText: { color: "#fff", fontSize: 17, fontWeight: "700" },
  testHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  testTitle: { fontSize: 20, fontWeight: "700", color: "#263d35" },
  testProgress: { fontSize: 14, color: "#545f59" },
  qNum: { fontSize: 13, fontWeight: "600", color: "#888", marginBottom: 4 },
  qCard: {
    backgroundColor: "#fff", borderRadius: 16, padding: 18, gap: 10,
    borderWidth: 1, borderColor: "#e2ddd3", marginBottom: 4,
  },
  qText: { fontSize: 17, fontWeight: "600", color: "#263d35", lineHeight: 26 },
  option: {
    flexDirection: "row", alignItems: "center", gap: 12,
    padding: 12, borderRadius: 12, backgroundColor: "#faf8f4",
    borderWidth: 1, borderColor: "#e2ddd3",
  },
  optionSelected: { backgroundColor: "#b73535", borderColor: "#b73535" },
  optionKey: {
    width: 28, height: 28, borderRadius: 14, backgroundColor: "#eee7df",
    textAlign: "center", lineHeight: 28, fontWeight: "700", fontSize: 14, color: "#263d35",
  },
  optionKeySelected: { backgroundColor: "rgba(255,255,255,0.3)", color: "#fff" },
  optionText: { flex: 1, fontSize: 15, color: "#263d35" },
  optionTextSelected: { color: "#fff" },
  cancelBtn: { flex: 1, backgroundColor: "#eee7df", borderRadius: 12, padding: 14, alignItems: "center" },
  cancelText: { fontWeight: "600", color: "#545f59", fontSize: 15 },
  submitBtn: { flex: 2, backgroundColor: "#b73535", borderRadius: 12, padding: 14, alignItems: "center" },
  submitBtnDisabled: { opacity: 0.5 },
  submitBtnText: { color: "#fff", fontWeight: "700", fontSize: 15 },
  scoreCard: { alignItems: "center", gap: 6 },
  bigScore: { fontSize: 56, fontWeight: "800" },
  scoreLabel: { fontSize: 16, color: "#545f59" },
  xpEarned: { fontSize: 18, fontWeight: "700", color: "#3a9e6b" },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: "#263d35" },
  qResult: {
    borderRadius: 14, padding: 14, gap: 6,
    borderWidth: 1, borderColor: "#e2ddd3", backgroundColor: "#fff",
  },
  qResultPass: { borderColor: "#b9d8c8", backgroundColor: "#f0faf5" },
  qResultFail: { borderColor: "#f0c8c8", backgroundColor: "#fff8f8" },
  qResultHeader: { flexDirection: "row", justifyContent: "space-between" },
  qResultNum: { fontWeight: "700", color: "#263d35" },
  correct: { color: "#3a9e6b", fontWeight: "700" },
  wrong: { color: "#b73535", fontWeight: "700" },
  qResultMeta: { fontSize: 14, color: "#545f59" },
  explanation: { fontSize: 13, color: "#888", fontStyle: "italic" },
});

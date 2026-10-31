import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, Button, Pressable, ScrollView, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api, useAuth } from "../hooks/useAuth";
import { emptyTestSession, useTestSession } from "../hooks/useTestSession";
import { Failure, Levels, ui } from "../components/StudyUI";
import { ApiError } from "../services/client";
import type { Answer, TestAttempt, TestHistory, TestResult } from "../services/contracts";

const CHOICES: Answer[] = ["A", "B", "C", "D"];
export default function TestsScreen() {
  const userId = useAuth(state => state.user?.id ?? null);
  const session = useTestSession();
  const [ready, setReady] = useState(false);
  const [level, setLevel] = useState("HSK1");
  const [count, setCount] = useState(20);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [history, setHistory] = useState<TestHistory[]>([]);
  const [historyBusy, setHistoryBusy] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const pending = useRef(false);
  useEffect(() => {
    let active = true;
    Promise.resolve(useTestSession.persist.rehydrate()).finally(() => {
      if (!active) return;
      if (useTestSession.getState().ownerId !== userId) useTestSession.setState({ ...emptyTestSession, ownerId: userId });
      setReady(true);
    });
    return () => { active = false; };
  }, [userId]);
  useFocusEffect(useCallback(() => {
    const controller = new AbortController();
    setHistoryBusy(true); setHistoryError("");
    api<TestHistory[]>("/tests/history?limit=20", { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) setHistory(data); })
      .catch(() => { if (!controller.signal.aborted) setHistoryError("Could not load previous attempts."); })
      .finally(() => { if (!controller.signal.aborted) setHistoryBusy(false); });
    return () => controller.abort();
  }, [historyRefresh]));
  const owned = session.ownerId === userId;
  const attempt = owned ? session.attempt : null;
  const result = owned ? session.result : null;
  const question = attempt?.questions[session.index];
  const answered = attempt?.questions.filter(q => session.answers[q.id]).length ?? 0;
  async function start() {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError("");
    try {
      const data = await api<TestAttempt>(`/tests/start?hsk_level=${level}&num_questions=${count}`, { method: "POST" });
      if (useAuth.getState().user?.id !== userId) return;
      if (!data.questions.length) throw new Error("No questions returned.");
      useTestSession.setState({ ...emptyTestSession, ownerId: userId, attempt: data });
      setConfirm(false);
    } catch (error) {
      setError(error instanceof ApiError && error.status === 404 ? "No practice questions are available for this level yet. Try another level." : "Could not start a practice test. Please try again.");
    } finally { pending.current = false; setBusy(false); }
  }
  async function submit() {
    if (pending.current || !attempt || session.submitted) return;
    pending.current = true; setBusy(true); setError("");
    try {
      const data = await api<TestResult>(`/tests/${attempt.attempt_id}/submit`, { method: "POST", body: JSON.stringify({ answers: session.answers }) });
      if (useAuth.getState().user?.id !== userId) return;
      useTestSession.setState({ result: data, submitted: true });
      const user = useAuth.getState().user;
      if (user) useAuth.setState({ user: { ...user, xp: user.xp + data.xp_gained } });
      setConfirm(false); setHistoryRefresh(n => n + 1);
    } catch (error) {
      if (useAuth.getState().user?.id !== userId) return;
      if (error instanceof ApiError && error.status === 409) {
        useTestSession.setState({ submitted: true });
        setConfirm(false); setHistoryRefresh(n => n + 1);
        setError("This attempt was already submitted. Its score is in recent attempts; detailed answers cannot be reloaded.");
      } else if (error instanceof ApiError && error.status === 404) {
        setError("This attempt is no longer available. You can leave it and start a new test.");
      } else {
        setError("Submission could not be confirmed. Your answers are kept. Retry submission; an already-saved attempt will not earn XP twice.");
      }
    } finally { pending.current = false; setBusy(false); }
  }
  function reset() {
    useTestSession.setState({ ...emptyTestSession, ownerId: userId });
    setConfirm(false); setError("");
  }
  if (!ready) return <ActivityIndicator accessibilityLabel="Restoring practice test" />;
  return <ScrollView contentContainerStyle={ui.page}>
    <Text style={ui.title}>HSK practice tests</Text>
    <Text style={ui.subtitle}>Vocabulary and pinyin practice for HSK 1–6. These quizzes are not full official HSK exams. Listening audio is not available yet.</Text>
    {!!error && <Text accessibilityRole="alert">{error}</Text>}
    {!attempt ? <>
      <Levels value={level} onChange={setLevel} disabled={busy} />
      <Text>Questions per practice</Text>
      <View style={ui.row}>{[10,20,40,60].map(n => <Pressable key={n} accessibilityRole="button" accessibilityLabel={`${n} questions`} accessibilityState={{ selected: count === n }} disabled={busy} style={[ui.chip, count === n && ui.selected]} onPress={() => setCount(n)}><Text>{n}</Text></Pressable>)}</View>
      <Button title={busy ? "Starting…" : "Start practice"} onPress={start} disabled={busy} color="#a63232" />
    </> : result ? <>
      <View style={ui.card}><Text style={ui.title}>{result.score_percent}% · {result.passed ? "Passed" : "Keep practising"}</Text><Text>{result.correct_answers} / {result.total_questions} correct · +{result.xp_gained} XP</Text><Text>Practice pass mark: 60%</Text></View>
      <Button title="Start another practice" onPress={reset} />
      <Text style={ui.pinyin}>Review your answers</Text>
      {result.results.map(item => {
        const q = attempt.questions.find(q => q.id === item.question_id);
        const option = (choice: Answer) => q?.[`option_${choice.toLowerCase()}` as "option_a"] ?? "";
        return <View key={item.question_id} style={ui.card}><Text>{q?.question_text ?? `Question ${item.question_id}`}</Text><Text>{item.is_correct ? "Correct" : "Incorrect"} · Your answer: {item.chosen ? `${item.chosen} · ${option(item.chosen)}` : "Unanswered"}</Text><Text>Correct answer: {item.correct} · {option(item.correct)}</Text>{!!item.explanation && <Text>{item.explanation}</Text>}</View>;
      })}
    </> : session.submitted ? <View style={ui.card}><Text>This attempt was submitted. See its score in recent attempts.</Text><Button title="Start another practice" onPress={reset} /></View> : question && <>
      <Text>{attempt.hsk_level} · Question {session.index + 1} of {attempt.total_questions} · {answered} answered</Text>
      <View style={ui.card}><Text style={ui.pinyin}>{question.question_text}</Text>
        {CHOICES.map(choice => <Pressable key={choice} accessibilityRole="radio" aria-checked={session.answers[question.id] === choice} aria-disabled={busy} disabled={busy} style={[ui.chip, session.answers[question.id] === choice && ui.selected]} onPress={() => { useTestSession.setState({ answers: { ...session.answers, [question.id]: choice } }); setConfirm(false); }}><Text>{choice} · {question[`option_${choice.toLowerCase()}` as "option_a"]}</Text></Pressable>)}
      </View>
      <View style={ui.row}><Button title="Previous question" disabled={busy || session.index === 0} onPress={() => { useTestSession.setState({ index: session.index - 1 }); setConfirm(false); }} /><Button title="Next question" disabled={busy || session.index >= attempt.questions.length - 1} onPress={() => { useTestSession.setState({ index: session.index + 1 }); setConfirm(false); }} /></View>
      {confirm ? <View style={ui.card}><Text>{attempt.total_questions - answered} unanswered. Unanswered questions count as incorrect. Submit this attempt?</Text><Button title={busy ? "Submitting…" : "Confirm submission"} disabled={busy} onPress={submit} color="#a63232" /><Button title="Keep answering" disabled={busy} onPress={() => setConfirm(false)} /></View> : <Button title="Finish practice" disabled={busy} onPress={() => setConfirm(true)} color="#a63232" />}
      <Text>Your draft is saved on this device. Return here to continue.</Text>
      {!!error && <Button title="Leave this attempt" disabled={busy} onPress={reset} />}
    </>}
    <Text style={ui.pinyin}>Recent attempts</Text>
    {historyBusy ? <ActivityIndicator accessibilityLabel="Loading attempt history" /> : historyError ? <Failure message={historyError} retry={() => setHistoryRefresh(n => n + 1)} /> : history.length === 0 ? <Text>No completed attempts yet.</Text> : history.map(item => <View key={item.id} style={ui.card}><Text>Attempt #{item.id} · {item.hsk_level} · {item.score_percent}% · {item.passed ? "Passed" : "Keep practising"}</Text><Text>{item.finished_at ? new Date(item.finished_at).toLocaleString() : ""}</Text></View>)}
    <Button title="Refresh history" disabled={historyBusy} onPress={() => setHistoryRefresh(n => n + 1)} />
  </ScrollView>;
}

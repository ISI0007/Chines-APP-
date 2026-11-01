import React, { useEffect, useState } from "react";
import { ActivityIndicator, Button, Pressable, ScrollView, Text, View } from "react-native";
import { FlashcardAPI, ReaderAPI, MockTestAPI, ProgressAPI, type MockResult, type MockTest } from "../services/api";
import { Levels, ui } from "../components/StudyUI";

export default function Phase2MockTestScreen() {
  const [level, setLevel] = useState("1"), [test, setTest] = useState<MockTest | null>(null), [result, setResult] = useState<MockResult | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({}), [index, setIndex] = useState(0), [seconds, setSeconds] = useState(0);
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  useEffect(() => { if (!test || result) return; const timer = setInterval(() => setSeconds(n => n + 1), 1000); return () => clearInterval(timer); }, [test, result]);
  async function start() { setBusy(true); setError(""); try { const next = await MockTestAPI.start(level); setTest(next); setResult(null); setAnswers({}); setIndex(0); setSeconds(0); } catch { setError("Could not start the mock test."); } finally { setBusy(false); } }
  async function submit() { if (!test || busy) return; setBusy(true); setError(""); try { setResult(await MockTestAPI.submit(test.id, answers)); } catch { setError("Could not submit answers. Retry to see your score."); } finally { setBusy(false); } }
  const question = test?.questions[index];
  return <ScrollView contentContainerStyle={ui.page}><Text style={ui.title}>HSK mock test</Text>
    {!test ? <><Levels value={`HSK${level}`} onChange={value => setLevel(value.replace("HSK", ""))} /><Button title={busy ? "Loading…" : "Start test"} disabled={busy} onPress={start} /></> : result ? <View style={ui.card}><Text style={ui.title}>Score: {result.score} / {result.total}</Text><Button title="Start another test" onPress={() => { setTest(null); setResult(null); }} /></View> : question ? <>
      <Text>Question {index + 1} / {test.questions.length} · {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</Text>
      <View style={ui.card}><Text style={ui.pinyin}>{question.question}</Text>{question.choices.map((choice, choiceIndex) => <Pressable key={choiceIndex} accessibilityRole="radio" accessibilityState={{ checked: answers[question.id] === choiceIndex }} onPress={() => setAnswers({ ...answers, [question.id]: choiceIndex })} style={[ui.chip, answers[question.id] === choiceIndex && ui.selected]}><Text>{choice}</Text></Pressable>)}</View>
      <View style={ui.row}><Button title="Previous" disabled={index === 0} onPress={() => setIndex(index - 1)} /><Button title="Next" disabled={index === test.questions.length - 1} onPress={() => setIndex(index + 1)} /></View>
      <Button title={busy ? "Submitting…" : "Submit test"} disabled={busy} onPress={submit} />
    </> : <Text>This test has no questions.</Text>}
    {!!error && <Text accessibilityRole="alert">{error}</Text>}
  </ScrollView>;
}


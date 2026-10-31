import React, { useCallback, useRef, useState } from "react";
import { ActivityIndicator, Animated, Button, Pressable, ScrollView, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api, useAuth } from "../hooks/useAuth";
import { Failure, Levels, ui } from "../components/StudyUI";
import { WordAudio } from "../components/WordAudio";
import type { ReviewResult, Word } from "../services/contracts";

const RATINGS = ["No recall", "Wrong; recognized answer", "Wrong; answer felt easy", "Correct with difficulty", "Correct after hesitation", "Perfect recall"];
export default function FlashcardScreen() {
  const [level, setLevel] = useState("HSK1");
  const [words, setWords] = useState<Word[]>([]);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [busy, setBusy] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [notice, setNotice] = useState("");
  const [retry, setRetry] = useState(0);
  const [earned, setEarned] = useState(0);
  const pending = useRef(false);
  const generation = useRef(0);
  const flip = useRef(new Animated.Value(0)).current;
  useFocusEffect(useCallback(() => {
    const controller = new AbortController();
    generation.current++;
    setBusy(true); setError(""); setWords([]); setIndex(0); setEarned(0); setRevealed(false); setSaveError(""); setNotice(""); flip.setValue(0);
    api<Word[]>(`/vocabulary/review?hsk_level=${level}&limit=20`, { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) setWords(data); })
      .catch(() => { if (!controller.signal.aborted) setError("Could not load your review queue."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => { controller.abort(); generation.current++; };
  }, [level, retry, flip]));
  const word = words[index];
  function reveal() {
    if (revealed || saving) return;
    setRevealed(true);
    Animated.timing(flip, { toValue: 1, duration: 300, useNativeDriver: true }).start();
  }
  async function rate(quality: number) {
    if (pending.current || !revealed || !word) return;
    pending.current = true; setSaving(true); setSaveError("");
    const current = generation.current;
    try {
      const result = await api<ReviewResult>("/vocabulary/review", { method: "POST", body: JSON.stringify({ word_id: word.id, quality }) });
      const user = useAuth.getState().user;
      if (user) useAuth.setState({ user: { ...user, xp: user.xp + result.xp_gained } });
      if (current !== generation.current) return;
      setEarned(n => n + result.xp_gained);
      setNotice(`+${result.xp_gained} XP · Next review: ${new Date(result.next_review).toLocaleDateString()}`);
      setIndex(i => i + 1); setRevealed(false); flip.setValue(0);
    } catch {
      if (current === generation.current) setSaveError("We could not confirm this rating was saved. Reload the queue before continuing to avoid counting it twice.");
    } finally { pending.current = false; setSaving(false); }
  }
  return <ScrollView contentContainerStyle={ui.page}>
    <Text style={ui.title}>A little practice, every day</Text>
    <Text style={ui.subtitle}>Recall the meaning before revealing the answer. Your rating sets the next review.</Text>
    <Levels value={level} onChange={setLevel} disabled={saving} />
    {!!notice && <Text accessibilityLiveRegion="polite">{notice}</Text>}
    {busy ? <ActivityIndicator accessibilityLabel="Loading review queue" /> : error ? <Failure message={error} retry={() => setRetry(n => n + 1)} /> : !word ? <View style={ui.card}><Text style={ui.title}>{words.length ? "Session complete" : "No words to review"}</Text><Text>{index} cards reviewed · {earned} XP earned this session</Text><Button title="Check for more words" onPress={() => setRetry(n => n + 1)} /></View> : <>
      <Text>Card {index + 1} of {words.length}</Text>
      <Pressable accessibilityRole="button" accessibilityLabel={revealed ? "Answer revealed" : `Reveal meaning for ${word.simplified} ${word.pinyin}`} onPress={reveal} disabled={revealed || saving}>
        <Animated.View style={[ui.card, { minHeight: 240, justifyContent: "center", transform: [{ perspective: 1000 }, { rotateY: flip.interpolate({ inputRange: [0, 0.5, 1], outputRange: ["0deg", "90deg", "0deg"] }) }] }]}>
          <View style={ui.row}><Text style={ui.hanzi}>{word.simplified}</Text><Text style={ui.pinyin}>{word.pinyin}</Text></View>
          {revealed ? <Text>{word.definitions.join("; ")}</Text> : <Text>Tap to reveal meaning</Text>}
        </Animated.View>
      </Pressable>
      {revealed && <WordAudio key={word.id} word={word} />}
      {revealed && <View style={ui.row}>{RATINGS.map((label, quality) => <Pressable key={quality} accessibilityRole="button" disabled={saving || !!saveError} onPress={() => rate(quality)} style={[ui.chip, { opacity: saving || saveError ? 0.5 : 1 }]}><Text>{quality} · {label}</Text></Pressable>)}</View>}
      {saving && <ActivityIndicator accessibilityLabel="Saving rating" />}
      {!!saveError && <Failure message={saveError} retry={() => setRetry(n => n + 1)} />}
    </>}
  </ScrollView>;
}

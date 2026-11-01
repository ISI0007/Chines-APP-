import React, { useEffect, useState } from "react";
import { ActivityIndicator, Button, Pressable, ScrollView, Text, View } from "react-native";
import { Failure, Levels, ui } from "../components/StudyUI";
import { FlashcardAPI, ReaderAPI, MockTestAPI, ProgressAPI, type Flashcard } from "../services/api";
import { Phase2WordAudio } from "../components/Phase2WordAudio";

export default function Phase2FlashcardScreen() {
  const [level, setLevel] = useState("1"), [retry, setRetry] = useState(0), [index, setIndex] = useState(0);
  const [words, setWords] = useState<Flashcard[]>([]);
  const [flipped, setFlipped] = useState(false), [busy, setBusy] = useState(true), [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setBusy(true); setError(""); setIndex(0); setFlipped(false);
    FlashcardAPI.list(level, controller.signal).then(data => { if (!controller.signal.aborted) setWords(data); })
      .catch(() => { if (!controller.signal.aborted) setError("Could not load flashcards."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [level, retry]);
  const word = words[index];
  async function review(quality: number) {
    if (!word || saving) return;
    setSaving(true); setError("");
    try { await FlashcardAPI.review(word.id, quality); setIndex(index + 1); setFlipped(false); }
    catch { setError("Could not save the review. Try again before moving on."); }
    finally { setSaving(false); }
  }
  return <ScrollView contentContainerStyle={ui.page}><Text style={ui.title}>Flashcards</Text>
    <Levels value={`HSK${level}`} onChange={value => setLevel(value.replace("HSK", ""))} disabled={saving} />
    {busy ? <ActivityIndicator /> : error && !word ? <Failure message={error} retry={() => setRetry(n => n + 1)} /> : !word ? <View style={ui.card}><Text>All cards reviewed.</Text><Button title="Reload cards" onPress={() => setRetry(n => n + 1)} /></View> : <>
      <Text>Card {index + 1} of {words.length}</Text>
      <Pressable accessibilityRole="button" onPress={() => setFlipped(true)} style={ui.card}><Text style={ui.hanzi}>{word.simplified}</Text><Text>{flipped ? `${word.pinyin} · ${word.meaning}` : "Tap to flip"}</Text></Pressable>
      {flipped && <><Phase2WordAudio word={word} /><View style={ui.row}>{[[1, "Again"], [3, "Hard"], [5, "Easy"]].map(([quality, label]) => <Button key={quality} title={String(label)} disabled={saving} onPress={() => review(Number(quality))} />)}</View></>}
      {!!error && <Text accessibilityRole="alert">{error}</Text>}
    </>}
  </ScrollView>;
}


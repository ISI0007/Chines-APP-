import React, { useEffect, useState } from "react";
import { ActivityIndicator, Button, ScrollView, Text, TextInput, View } from "react-native";
import { Audio } from "expo-av";
import { API_BASE } from "../constants/api";
import { audioUrl, ttsUrl } from "../services/audio";
import { FlashcardAPI, ReaderAPI, MockTestAPI, ProgressAPI, type Flashcard } from "../services/api";
import { Failure, Levels, ui } from "../components/StudyUI";

export default function AudioDrillScreen() {
  const [level, setLevel] = useState("1");
  const [words, setWords] = useState<Flashcard[]>([]);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setBusy(true); setError(""); setWords([]); setIndex(0); setAnswer(""); setChecked(false);
    FlashcardAPI.list(level, controller.signal).then(data => { if (!controller.signal.aborted) setWords(data); })
      .catch(() => { if (!controller.signal.aborted) setError("Could not load audio drills."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [level, retry]);
  const word = words[index];
  async function play() {
    if (!word || playing) return;
    setPlaying(true);
    let sound: Audio.Sound | null = null;
    try {
      const uri = word.audio_path ? audioUrl(API_BASE, word.audio_path) : ttsUrl(word.simplified);
      sound = (await Audio.Sound.createAsync({ uri }, { shouldPlay: true })).sound;
      await new Promise<void>(resolve => sound?.setOnPlaybackStatusUpdate(status => {
        if (!status.isLoaded || status.didJustFinish) resolve();
      }));
    } catch { setError("Audio could not be played."); }
    finally { await sound?.unloadAsync().catch(() => {}); setPlaying(false); }
  }
  return <ScrollView contentContainerStyle={ui.page}>
    <Text style={ui.title}>Audio drill</Text><Text style={ui.subtitle}>Listen, then type the word you heard.</Text>
    <Levels value={`HSK${level}`} onChange={value => setLevel(value.replace("HSK", ""))} />
    {busy ? <ActivityIndicator /> : error ? <Failure message={error} retry={() => { setError(""); setRetry(n => n + 1); }} /> : !word ? <Text>No recorded words are available for this level.</Text> : <View style={ui.card}>
      <Text>Word {index + 1} of {words.length}</Text>
      <Button title={playing ? "Playing…" : "Play word"} disabled={playing} onPress={play} />
      <TextInput accessibilityLabel="Word heard" value={answer} onChangeText={setAnswer} autoCorrect={false} placeholder="Type Chinese characters or pinyin" style={{ borderWidth: 1, borderColor: "#aaa", borderRadius: 8, padding: 12 }} />
      {checked ? <><Text accessibilityLiveRegion="polite">{answer.trim().toLowerCase() === word.simplified.toLowerCase() || answer.trim().toLowerCase() === word.pinyin.toLowerCase() ? "Correct!" : `Answer: ${word.simplified} · ${word.pinyin} · ${word.meaning}`}</Text><Button title="Next word" onPress={() => { setIndex((index + 1) % words.length); setAnswer(""); setChecked(false); }} /></> : <Button title="Check answer" disabled={!answer.trim()} onPress={() => setChecked(true)} />}
    </View>}
  </ScrollView>;
}


import React, { useEffect, useRef, useState } from "react";
import { Button, Text } from "react-native";
import { Audio } from "expo-av";
import { API_BASE } from "../constants/api";
import { audioUrl, ttsUrl } from "../services/audio";
import type { Flashcard } from "../services/contracts";

export function Phase2WordAudio({ word }: { word: Flashcard }) {
  const sound = useRef<Audio.Sound | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => () => { void sound.current?.unloadAsync(); }, [word.id]);
  async function play() {
    if (busy) return;
    setBusy(true); setError("");
    try {
      await sound.current?.unloadAsync();
      const uri = word.audio_path ? audioUrl(API_BASE, word.audio_path) : ttsUrl(word.simplified);
      sound.current = (await Audio.Sound.createAsync({ uri }, { shouldPlay: true })).sound;
    } catch { setError("Audio unavailable. Try again."); }
    finally { setBusy(false); }
  }
  return <><Button title={busy ? "Loading audio…" : "Listen"} disabled={busy} onPress={play} />{!!error && <Text accessibilityRole="alert">{error}</Text>}</>;
}

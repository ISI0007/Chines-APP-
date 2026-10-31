import React, { useEffect, useRef, useState } from "react";
import { Button, Text, View } from "react-native";
import { Audio } from "expo-av";
import { useIsFocused } from "@react-navigation/native";
import { API_BASE } from "../constants/api";
import { audioUrl, ttsUrl } from "../services/audio";
import type { Word } from "../services/contracts";
export function WordAudio({ word }: { word: Word }) {
  const sound = useRef<Audio.Sound | null>(null);
  const generation = useRef(0);
  const inFlight = useRef(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const focused = useIsFocused();
  useEffect(() => {
    setBusy(false); setMessage(""); inFlight.current = false;
    return () => { generation.current++; void sound.current?.unloadAsync().catch(() => {}); sound.current = null; };
  }, [word.id, focused]);
  async function play() {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setMessage("");
    const current = generation.current;
    let candidate: Audio.Sound | null = null;
    try {
      await sound.current?.unloadAsync(); sound.current = null;
      const playUri = async (uri: string) => {
        candidate = (await Audio.Sound.createAsync({ uri }, { shouldPlay: false })).sound;
        if (current !== generation.current) { await candidate.unloadAsync(); return false; }
        sound.current = candidate;
        // Web can defer a missing-file error until playAsync, after load succeeds.
        await candidate.playAsync();
        return true;
      };
      if (word.audio_path) {
        try { await playUri(audioUrl(API_BASE, word.audio_path)); return; }
        catch { await (sound.current as Audio.Sound | null)?.unloadAsync().catch(() => {}); sound.current = null; }
      }
      if (current !== generation.current) return;
      if (await playUri(ttsUrl(word.simplified)) && current === generation.current) setMessage("Synthetic pronunciation · Google TTS");
    } catch {
      await sound.current?.unloadAsync().catch(() => {});
      if (current === generation.current) setMessage("Audio unavailable. Check your connection and try again.");
    } finally { if (current === generation.current) { setBusy(false); inFlight.current = false; } }
  }
  return <View style={{ gap: 8 }}><Button title={busy ? "Loading audio…" : "Listen"} disabled={busy || !focused} onPress={play} color="#a63232" />{!!message && <Text accessibilityLiveRegion="polite">{message}</Text>}</View>;
}

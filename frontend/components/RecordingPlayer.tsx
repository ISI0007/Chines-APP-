import React, { useEffect, useRef, useState } from "react";
import { Button, Text, View } from "react-native";
import { useIsFocused } from "@react-navigation/native";
import { Audio } from "expo-av";
import { API_BASE } from "../constants/api";
import { audioUrl } from "../services/audio";

/** Passage audio only: never substitute word recordings or synthesize a long passage. */
export function RecordingPlayer({ path }: { path: string | null }) {
  const sound = useRef<Audio.Sound | null>(null);
  const generation = useRef(0);
  const pending = useRef(false);
  const [busy, setBusy] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState("");
  const focused = useIsFocused();
  useEffect(() => {
    setPlaying(false); setBusy(false); setError(""); pending.current = false;
    return () => { generation.current++; void sound.current?.unloadAsync().catch(() => {}); sound.current = null; };
  }, [path, focused]);
  async function toggle() {
    if (!path || pending.current) return;
    pending.current = true; setBusy(true); setError("");
    const current = generation.current;
    try {
      await sound.current?.unloadAsync(); sound.current = null;
      if (playing) { setPlaying(false); return; }
      const { sound: loaded } = await Audio.Sound.createAsync({ uri: audioUrl(API_BASE, path) }, { shouldPlay: false });
      if (generation.current !== current) { await loaded.unloadAsync(); return; }
      sound.current = loaded;
      loaded.setOnPlaybackStatusUpdate(status => {
        if (generation.current !== current) return;
        if (status.isLoaded && status.didJustFinish) setPlaying(false);
        if (!status.isLoaded && status.error) { setPlaying(false); setError("This recording could not be played. Try again."); }
      });
      await loaded.playAsync();
      if (generation.current === current) setPlaying(true);
    } catch {
      if (generation.current === current) { setPlaying(false); setError("This recording could not be played. Try again."); }
      await sound.current?.unloadAsync().catch(() => {});
    } finally { if (generation.current === current) { pending.current = false; setBusy(false); } }
  }
  return <View style={{ gap: 10 }}>{path
    ? <Button title={busy ? "Loading recording…" : playing ? "Stop recording" : "Listen to passage"} onPress={toggle} disabled={busy || !focused} color="#a63232" />
    : <Text>No passage recording is available yet.</Text>}
    {!!error && <Text accessibilityRole="alert">{error}</Text>}
  </View>;
}

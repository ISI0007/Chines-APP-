import React, { useEffect, useRef, useState } from "react";
import { Pressable, Text, View } from "react-native";
import { useIsFocused } from "@react-navigation/native";
import { Audio } from "expo-av";
import { API_BASE } from "../constants/api";
import { audioUrl, ttsUrl } from "../services/audio";

/** Play the supplied narration, or sentence-sized TTS parts when no recording exists. */
export function RecordingPlayer({ path, text }: { path: string | null; text: string }) {
  const sound = useRef<Audio.Sound | null>(null);
  const generation = useRef(0);
  const pending = useRef(false);
  const [busy, setBusy] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState("");
  const sequence = useRef(0);
  const focused = useIsFocused();
  useEffect(() => {
    setPlaying(false); setBusy(false); setError(""); pending.current = false; sequence.current++;
    return () => { generation.current++; sequence.current++; void sound.current?.unloadAsync().catch(() => {}); sound.current = null; };
  }, [path, focused]);
  function chunks(value: string) {
    const sentences = value.match(/[^。！？.!?]+[。！？.!?]?/g)?.map(part => part.trim()).filter(Boolean) ?? [];
    return sentences.flatMap(sentence => sentence.length <= 180 ? [sentence] : sentence.match(/.{1,150}/gu) ?? [sentence]);
  }
  async function playNext(parts: string[], index: number, run: number) {
    if (run !== sequence.current || index >= parts.length) { if (run === sequence.current) setPlaying(false); return; }
    try {
      const { sound: loaded } = await Audio.Sound.createAsync({ uri: ttsUrl(parts[index]) }, { shouldPlay: false });
      if (run !== sequence.current) { await loaded.unloadAsync(); return; }
      sound.current = loaded;
      let advanced = false;
      loaded.setOnPlaybackStatusUpdate(status => {
        if (run !== sequence.current || advanced) return;
        if (status.isLoaded && status.didJustFinish) {
          advanced = true;
          void loaded.unloadAsync(); sound.current = null;
          void playNext(parts, index + 1, run);
        }
        if (!status.isLoaded && status.error) { setPlaying(false); setError("Story audio could not be played. Check your connection and try again."); }
      });
      await loaded.playAsync();
      if (run === sequence.current) setPlaying(true);
    } catch {
      if (run === sequence.current) { setPlaying(false); setError("Story audio could not be played. Check your connection and try again."); }
    }
  }
  async function toggle() {
    if (pending.current) return;
    if (playing) { sequence.current++; await sound.current?.stopAsync().catch(() => {}); await sound.current?.unloadAsync().catch(() => {}); sound.current = null; setPlaying(false); setBusy(false); return; }
    pending.current = true; setBusy(true); setError("");
    const current = generation.current;
    try {
      await sound.current?.unloadAsync(); sound.current = null;
      if (path) {
        try {
          const { sound: loaded } = await Audio.Sound.createAsync({ uri: audioUrl(API_BASE, path) }, { shouldPlay: false });
          if (generation.current !== current) { await loaded.unloadAsync(); return; }
          sound.current = loaded;
          loaded.setOnPlaybackStatusUpdate(status => { if (generation.current !== current) return; if (status.isLoaded && status.didJustFinish) setPlaying(false); if (!status.isLoaded && status.error) { setPlaying(false); setError("This recording could not be played. Starting speech audio instead."); void playNext(chunks(text), 0, ++sequence.current); } });
          await loaded.playAsync();
          if (generation.current === current) setPlaying(true);
          return;
        } catch { /* Fall back to sentence-sized speech audio below. */ }
      }
      const parts = chunks(text); if (!parts.length) throw new Error("No story text");
      const run = ++sequence.current; await playNext(parts, 0, run);
    } catch {
      if (generation.current === current) { setPlaying(false); setError("This recording could not be played. Try again."); }
      await sound.current?.unloadAsync().catch(() => {});
    } finally { if (generation.current === current) { pending.current = false; setBusy(false); } }
  }
  return <View style={{ gap: 8 }}>
    <Pressable accessibilityRole="button" accessibilityLabel={playing ? "Stop story audio" : "Listen to the whole story"} onPress={toggle} disabled={busy || !focused} style={{borderRadius:16,backgroundColor:"#E9EFE5",padding:15,flexDirection:"row",alignItems:"center",gap:12,opacity:busy?0.7:1}}>
      <View style={{flex:1}}><Text style={{fontSize:14,fontWeight:"800",color:"#304C37"}}>Listen & read</Text><Text style={{fontSize:11,color:"#737D70",marginTop:3}}>{busy ? "Loading audio…" : playing ? "Playing story audio · tap to stop" : path ? "Narrated story audio" : "Sentence-by-sentence speech audio"}</Text></View>
      <View style={{width:40,height:40,borderRadius:20,backgroundColor:"#315B43",alignItems:"center",justifyContent:"center"}}><Text style={{fontSize:13,color:"#fff",marginLeft:playing?0:2}}>{playing ? "■" : "▶"}</Text></View>
    </Pressable>
    {!!error && <Text accessibilityRole="alert" style={{fontSize:12,color:"#9A4D42"}}>{error}</Text>}
  </View>;
}

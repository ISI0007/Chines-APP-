import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, Text, View } from "react-native";
import { router } from "expo-router";
import { useContent } from "../hooks/useContent";
import { Failure, Levels, ui } from "../components/StudyUI";
import type { ReadingSummary } from "../services/contracts";

export default function ReadingScreen() {
  const [level, setLevel] = useState("HSK1");
  const [topic, setTopic] = useState<string | null>(null);
  const { data, loading, error, reload } = useContent<ReadingSummary[]>(`/reading/texts?hsk_level=${level}`);
  const topics = Array.from(new Set(data?.map(item => item.topic) ?? []));
  const visible = data?.filter(item => !topic || item.topic === topic) ?? [];
  return <ScrollView contentContainerStyle={ui.page}>
    <Text style={ui.title}>A little story, a little progress</Text>
    <Text style={ui.subtitle}>Read at your own pace, with pinyin and English when you need them.</Text>
    <Text>Current reading library: HSK1 only. More levels are coming.</Text>
    <Levels value={level} onChange={value => { setLevel(value); setTopic(null); }} />
    {loading ? <ActivityIndicator accessibilityLabel="Loading reading library" /> : error ? <Failure message={error} retry={reload} /> : <>
      {!!data?.length && <View style={ui.row}>{[null, ...topics].map(value => <Pressable key={value ?? "all"} accessibilityRole="button" aria-pressed={topic === value} onPress={() => setTopic(value)} style={[ui.chip, topic === value && ui.selected]}><Text>{value ?? "All topics"}</Text></Pressable>)}</View>}
      {!visible.length && <Text>{level === "HSK1" ? "No reading texts available here yet. Try another topic or check back later." : `No ${level} reading texts yet. Choose HSK1 to start reading.`}</Text>}
      {visible.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Read ${item.title}`} style={ui.card} onPress={() => router.push({ pathname: "/reading/[id]", params: { id: item.id } })}>
        <Text style={ui.pinyin}>{item.title}</Text><Text>{item.title_pinyin}</Text>
        <Text>{item.hsk_level} · {item.topic} · {item.word_count} words</Text><Text>{item.completed ? "Completed" : "Read story →"}</Text>
      </Pressable>)}
    </>}
  </ScrollView>;
}

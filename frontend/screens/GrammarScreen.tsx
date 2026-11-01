import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, Text } from "react-native";
import { router } from "expo-router";
import { useContent } from "../hooks/useContent";
import { Failure, Levels, ui } from "../components/StudyUI";
import type { GrammarSummary } from "../services/contracts";

export default function GrammarScreen() {
  const [level, setLevel] = useState("HSK1");
  const { data, loading, error, reload } = useContent<GrammarSummary[]>(`/grammar/lessons?hsk_level=${level}`);
  return <ScrollView contentContainerStyle={ui.page}>
    <Text style={ui.title}>Make your words work together</Text>
    <Text style={ui.subtitle}>Learn a pattern, explore examples, and build more confident sentences.</Text>
    <Text>Current grammar library: HSK1 only. More levels are coming.</Text>
    <Levels value={level} onChange={setLevel} />
    {loading ? <ActivityIndicator accessibilityLabel="Loading grammar library" /> : error ? <Failure message={error} retry={reload} /> : <>
      {!data?.length && <Text>{level === "HSK1" ? "No grammar lessons available yet. Check back later." : `No ${level} grammar lessons yet. Choose HSK1 to start learning.`}</Text>}
      {data?.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Study ${item.title}`} style={ui.card} onPress={() => router.push({ pathname: "/grammar/[id]", params: { id: item.id } })}>
        <Text style={ui.pinyin}>{item.title}</Text><Text style={ui.subtitle}>{item.pattern}</Text>
        <Text>{item.hsk_level} · {item.completed ? "Completed" : "Open lesson →"}</Text>
      </Pressable>)}
    </>}
  </ScrollView>;
}

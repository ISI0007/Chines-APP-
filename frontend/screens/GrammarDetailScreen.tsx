import React, { useState } from "react";
import { ActivityIndicator, ScrollView, Text, View } from "react-native";
import { Link } from "expo-router";
import { useContent } from "../hooks/useContent";
import { Failure, ui } from "../components/StudyUI";
import { StudyToggle } from "../components/StudyToggle";
import { CompletionButton } from "../components/CompletionButton";
import type { GrammarDetail } from "../services/contracts";

export default function GrammarDetailScreen({ id }: { id: string }) {
  const path = /^[1-9]\d*$/.test(id) ? `/grammar/lessons/${id}` : null;
  const { data, setData, loading, error, reload } = useContent<GrammarDetail>(path);
  const [pinyin, setPinyin] = useState(true);
  const [translation, setTranslation] = useState(true);
  return <ScrollView contentContainerStyle={ui.page}>
    <Link href="/grammar" style={ui.pinyin}>← Grammar library</Link>
    {loading ? <ActivityIndicator accessibilityLabel="Loading grammar lesson" /> : error ? <Failure message={error} retry={reload} /> : data && <>
      <Text style={ui.title}>{data.title}</Text><Text>{data.hsk_level}</Text>
      <View style={ui.card}><Text style={ui.pinyin}>Sentence pattern</Text><Text selectable style={{ fontSize: 24, lineHeight: 36 }}>{data.pattern}</Text></View>
      <Text selectable style={ui.subtitle}>{data.explanation}</Text>
      <Text style={ui.pinyin}>Examples</Text>
      <View style={ui.row}><StudyToggle label="Pinyin" value={pinyin} onChange={setPinyin} /><StudyToggle label="Translation" value={translation} onChange={setTranslation} /></View>
      {data.examples.map((example, index) => <View key={index} style={ui.card}>
        <Text selectable style={{ fontSize: 26, lineHeight: 40, color: "#263d35" }}>{example.zh}</Text>
        {pinyin && <Text selectable style={{ fontSize: 18, lineHeight: 30, color: "#a63232" }}>{example.pinyin}</Text>}
        {translation && <Text selectable style={ui.subtitle}>{example.en}</Text>}
      </View>)}
      <CompletionButton path={`${path}/complete`} completed={data.completed} label="Complete lesson" onComplete={() => setData(value => value ? { ...value, completed: true } : value)} />
    </>}
  </ScrollView>;
}

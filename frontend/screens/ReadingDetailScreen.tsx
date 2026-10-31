import React, { useState } from "react";
import { ActivityIndicator, ScrollView, Text, View } from "react-native";
import { Link } from "expo-router";
import { useContent } from "../hooks/useContent";
import { Failure, ui } from "../components/StudyUI";
import { StudyToggle } from "../components/StudyToggle";
import { CompletionButton } from "../components/CompletionButton";
import { RecordingPlayer } from "../components/RecordingPlayer";
import type { ReadingDetail } from "../services/contracts";

export default function ReadingDetailScreen({ id }: { id: string }) {
  const path = /^[1-9]\d*$/.test(id) ? `/reading/texts/${id}` : null;
  const { data, setData, loading, error, reload } = useContent<ReadingDetail>(path);
  const [pinyin, setPinyin] = useState(false);
  const [translation, setTranslation] = useState(false);
  const [large, setLarge] = useState(false);
  return <ScrollView contentContainerStyle={ui.page}>
    <Link href="/reading" style={ui.pinyin}>← Reading library</Link>
    {loading ? <ActivityIndicator accessibilityLabel="Loading story" /> : error ? <Failure message={error} retry={reload} /> : data && <>
      <Text style={ui.title}>{data.title}</Text><Text style={ui.pinyin}>{data.title_pinyin}</Text>
      <Text>{data.hsk_level} · {data.topic} · {data.word_count} words</Text>
      <View style={ui.row}><StudyToggle label="Pinyin" value={pinyin} onChange={setPinyin} /><StudyToggle label="Translation" value={translation} onChange={setTranslation} /><StudyToggle label="Larger text" value={large} onChange={setLarge} activeText="Use standard text" inactiveText="Use larger text" /></View>
      <View style={ui.card}><Text selectable style={{ fontSize: large ? 32 : 25, lineHeight: large ? 52 : 42, color: "#263d35" }}>{data.content}</Text></View>
      {pinyin && <View style={ui.card}><Text style={ui.pinyin}>Passage pinyin</Text><Text selectable style={{ fontSize: 19, lineHeight: 32 }}>{data.content_pinyin}</Text></View>}
      {translation && <View style={ui.card}><Text style={ui.pinyin}>English translation</Text><Text selectable style={ui.subtitle}>{data.translation}</Text></View>}
      <RecordingPlayer path={data.audio_path} />
      <CompletionButton path={`${path}/complete`} completed={data.completed} label="Mark as read" onComplete={() => setData(value => value ? { ...value, completed: true } : value)} />
    </>}
  </ScrollView>;
}

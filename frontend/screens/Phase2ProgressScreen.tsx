import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, Text, View } from "react-native";
import { Failure, ui } from "../components/StudyUI";
import { FlashcardAPI, ReaderAPI, MockTestAPI, ProgressAPI, type Phase2Progress } from "../services/api";

export default function Phase2ProgressScreen() {
  const [data, setData] = useState<Phase2Progress | null>(null), [busy, setBusy] = useState(true), [error, setError] = useState(""), [retry, setRetry] = useState(0);
  useEffect(() => { const controller = new AbortController(); setBusy(true); setError(""); ProgressAPI.me(controller.signal).then(value => { if (!controller.signal.aborted) setData(value); }).catch(() => { if (!controller.signal.aborted) setError("Could not load progress."); }).finally(() => { if (!controller.signal.aborted) setBusy(false); }); return () => controller.abort(); }, [retry]);
  const goal = Math.max(1, data?.next_level_xp ?? 100);
  return <ScrollView contentContainerStyle={ui.page}><Text style={ui.title}>Your progress</Text>{busy ? <ActivityIndicator /> : error ? <Failure message={error} retry={() => setRetry(n => n + 1)} /> : data && <>
    <View style={ui.card}><Text style={ui.title}>{data.xp} XP</Text><View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: goal, now: Math.min(data.xp, goal) }} style={{ height: 12, backgroundColor: "#eee7df", borderRadius: 6 }}><View style={{ height: 12, width: `${Math.min(100, data.xp / goal * 100)}%`, backgroundColor: "#42745b", borderRadius: 6 }} /></View><Text>{data.streak} day streak · {data.words_learned} words learned</Text></View>
    <Text style={ui.pinyin}>Activity</Text><View style={ui.row}>{data.activity?.length ? data.activity.map(day => <View key={day.date} accessibilityLabel={`${day.date}: ${day.count} reviews`} style={{ width: 22, height: 22, backgroundColor: day.count ? "#42745b" : "#eee7df", borderRadius: 4 }} />) : <Text>No activity history available yet.</Text>}</View>
  </>}</ScrollView>;
}


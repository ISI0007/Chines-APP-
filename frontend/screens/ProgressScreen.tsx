import React, { useCallback, useState } from "react";
import { ActivityIndicator, Button, ScrollView, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api, useAuth } from "../hooks/useAuth";
import { Failure, ui } from "../components/StudyUI";
import type { Progress } from "../services/contracts";
export default function ProgressScreen() {
  const [data, setData] = useState<Progress | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useFocusEffect(useCallback(() => {
    const controller = new AbortController(); setBusy(true); setError("");
    api<Progress>("/vocabulary/progress", { signal: controller.signal }).then(result => {
      if (controller.signal.aborted) return;
      setData(result);
      const user = useAuth.getState().user;
      if (user) useAuth.setState({ user: { ...user, xp: result.user_xp, streak_days: result.streak_days } });
    }).catch(() => { if (!controller.signal.aborted) setError("Could not load your progress."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [retry]));
  return <ScrollView contentContainerStyle={ui.page}><Text style={ui.title}>See how far you’ve come</Text>
    {busy ? <ActivityIndicator accessibilityLabel="Loading progress" /> : error ? <Failure message={error} retry={() => setRetry(n => n + 1)} /> : data && <>
      <View style={ui.card}><Text style={ui.title}>{data.user_xp} XP</Text><Text>{data.streak_days} day streak · Tracking not active yet</Text></View>
      <Text>Progress covers imported HSK 3.0 vocabulary. Each level counts words introduced at that level, not cumulative totals.</Text>
      {Object.entries(data.levels).sort(([a], [b]) => a.localeCompare(b)).map(([level, progress]) => {
        const percent = progress.total > 0 ? Math.min(100, Math.max(0, progress.learned / progress.total * 100)) : 0;
        return <View key={level} style={ui.card}><Text style={ui.pinyin}>{level}</Text><Text>{progress.learned} / {progress.total} words learned</Text><View accessibilityRole="progressbar" accessibilityLabel={`${level} words learned`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(percent)} style={{ height: 12, borderRadius: 6, backgroundColor: "#eee7df", overflow: "hidden" }}><View style={{ width: `${percent}%`, height: 12, backgroundColor: "#42745b" }} /></View><Text>{progress.due_for_review} due for review{progress.total === 0 ? " · No vocabulary imported yet" : ""}</Text></View>;
      })}<Button title="Refresh progress" onPress={() => setRetry(n => n + 1)} />
    </>}
  </ScrollView>;
}


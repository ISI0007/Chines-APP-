import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { router } from "expo-router";
import { api } from "../hooks/useAuth";
import { Failure, ui } from "../components/StudyUI";
import type { CourseLevelSummary, CourseLevelsResponse } from "../services/contracts";

function LevelCard({ level, onPress }: { level: CourseLevelSummary; onPress(): void }) {
  const pct = Math.round((level.completion_pct ?? 0) * 100);
  const done = pct >= 100;
  return (
    <TouchableOpacity style={[s.levelCard, done && s.levelDone]} onPress={onPress} accessibilityRole="button">
      <View style={s.levelHeader}>
        <Text style={s.levelName}>{level.hsk_level}</Text>
        {done && <Text style={s.badge}>✓ Done</Text>}
      </View>
      <Text style={s.levelMeta}>{level.total_lessons} lessons · {level.completed_lessons} completed</Text>
      <View style={s.progressBg}>
        <View style={[s.progressFill, { width: `${pct}%` as any }]} />
      </View>
      <Text style={s.progressLabel}>{pct}%</Text>
    </TouchableOpacity>
  );
}

export default function CourseScreen() {
  const [levels, setLevels] = useState<CourseLevelSummary[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useFocusEffect(useCallback(() => {
    setBusy(true); setError("");
    const controller = new AbortController();
    api<CourseLevelsResponse>("/course/levels", { signal: controller.signal })
      .then(r => { if (!controller.signal.aborted) setLevels(r.levels); })
      .catch(() => { if (!controller.signal.aborted) setError("Could not load course levels."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [retry]));

  return (
    <ScrollView style={styles.container} contentContainerStyle={ui.page}>
      <Text style={ui.title}>📚 HSK Course</Text>
      <Text style={ui.subtitle}>Work through structured lessons for each HSK level.</Text>

      {busy && <ActivityIndicator color="#b73535" style={{ marginTop: 20 }} />}
      {!!error && <Failure message={error} retry={() => setRetry(r => r + 1)} />}

      {levels.map(level => (
        <LevelCard
          key={level.hsk_level}
          level={level}
          onPress={() => router.push({ pathname: "/course/units", params: { level: level.hsk_level } })}
        />
      ))}

      {!busy && levels.length === 0 && !error && (
        <View style={ui.card}>
          <Text style={{ color: "#545f59" }}>No course content available yet.</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { flex: 1, backgroundColor: "#faf8f4" } });
const s = StyleSheet.create({
  levelCard: {
    backgroundColor: "#fff", borderRadius: 18, padding: 20, gap: 8,
    borderWidth: 1, borderColor: "#e2ddd3",
  },
  levelDone: { borderColor: "#3a9e6b", backgroundColor: "#f0faf5" },
  levelHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  levelName: { fontSize: 20, fontWeight: "700", color: "#263d35" },
  badge: { fontSize: 13, color: "#3a9e6b", fontWeight: "600" },
  levelMeta: { fontSize: 14, color: "#545f59" },
  progressBg: { height: 8, borderRadius: 4, backgroundColor: "#eee7df", overflow: "hidden" },
  progressFill: { height: 8, borderRadius: 4, backgroundColor: "#b73535" },
  progressLabel: { fontSize: 12, color: "#888", textAlign: "right" },
});

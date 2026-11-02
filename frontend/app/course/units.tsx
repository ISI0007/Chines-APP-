import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";
import { api } from "../../hooks/useAuth";
import { Failure, ui } from "../../components/StudyUI";
import { Protected } from "../../components/StudyUI";
import type { CourseLessonItem, CourseUnitsResponse } from "../../services/contracts";

function LessonRow({ lesson, onPress }: { lesson: CourseLessonItem; onPress(): void }) {
  return (
    <TouchableOpacity
      style={[s.lessonRow, lesson.completed && s.lessonDone]}
      onPress={onPress}
      accessibilityRole="button"
    >
      <Text style={s.lessonEmoji}>{lesson.completed ? "✅" : "📄"}</Text>
      <View style={s.lessonInfo}>
        <Text style={s.lessonTitle}>{lesson.title_en}</Text>
        <Text style={s.lessonMeta}>Lesson {lesson.lesson_number} · {lesson.topic}</Text>
      </View>
      <Text style={s.arrow}>›</Text>
    </TouchableOpacity>
  );
}

function UnitsView() {
  const { level } = useLocalSearchParams<{ level: string }>();
  const [data, setData] = useState<CourseUnitsResponse | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useFocusEffect(useCallback(() => {
    if (!level) return;
    setBusy(true); setError("");
    const controller = new AbortController();
    api<CourseUnitsResponse>(`/course/units?hsk_level=${level}`, { signal: controller.signal })
      .then(r => { if (!controller.signal.aborted) setData(r); })
      .catch(() => { if (!controller.signal.aborted) setError("Could not load lessons."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [level, retry]));

  return (
    <ScrollView style={styles.container} contentContainerStyle={ui.page}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Text style={s.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={s.levelBadge}>{level}</Text>
      </View>

      <Text style={ui.title}>Lessons</Text>

      {busy && <ActivityIndicator color="#b73535" style={{ marginTop: 20 }} />}
      {!!error && <Failure message={error} retry={() => setRetry(r => r + 1)} />}

      {data?.lessons.map(lesson => (
        <LessonRow
          key={lesson.id}
          lesson={lesson}
          onPress={() => router.push({ pathname: "/course/lesson", params: { id: String(lesson.id) } })}
        />
      ))}

      {!busy && !error && data?.lessons.length === 0 && (
        <View style={ui.card}>
          <Text style={{ color: "#545f59" }}>No lessons available for {level} yet.</Text>
        </View>
      )}
    </ScrollView>
  );
}

export default function UnitsRoute() {
  return <Protected><UnitsView /></Protected>;
}

const styles = StyleSheet.create({ container: { flex: 1, backgroundColor: "#faf8f4" } });
const s = StyleSheet.create({
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  backBtn: { padding: 4 },
  backText: { fontSize: 15, color: "#b73535", fontWeight: "600" },
  levelBadge: {
    backgroundColor: "#eee7df", borderRadius: 10, paddingHorizontal: 12, paddingVertical: 4,
    fontSize: 13, fontWeight: "700", color: "#263d35",
  },
  lessonRow: {
    flexDirection: "row", alignItems: "center", gap: 14,
    backgroundColor: "#fff", borderRadius: 14, padding: 16,
    borderWidth: 1, borderColor: "#e2ddd3",
  },
  lessonDone: { backgroundColor: "#f0faf5", borderColor: "#b9d8c8" },
  lessonEmoji: { fontSize: 22, width: 28, textAlign: "center" },
  lessonInfo: { flex: 1, gap: 2 },
  lessonTitle: { fontSize: 15, fontWeight: "600", color: "#263d35" },
  lessonMeta: { fontSize: 13, color: "#888" },
  arrow: { fontSize: 20, color: "#bbb" },
});

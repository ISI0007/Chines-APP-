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
import { api, useAuth } from "../hooks/useAuth";
import { Failure, ui } from "../components/StudyUI";
import type { CourseLessonDetail, LessonCompleteResult } from "../services/contracts";

export default function LessonScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const [lesson, setLesson] = useState<CourseLessonDetail | null>(null);
  const [busy, setBusy] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [result, setResult] = useState<LessonCompleteResult | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useFocusEffect(useCallback(() => {
    if (!id) return;
    setBusy(true); setError(""); setResult(null);
    const controller = new AbortController();
    api<CourseLessonDetail>(`/course/lessons/${id}`, { signal: controller.signal })
      .then(r => { if (!controller.signal.aborted) setLesson(r); })
      .catch(() => { if (!controller.signal.aborted) setError("Could not load lesson."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [id, retry]));

  async function complete() {
    if (!id || completing) return;
    setCompleting(true); setError("");
    try {
      const r = await api<LessonCompleteResult>(`/course/lessons/${id}/complete`, { method: "POST" });
      setResult(r);
      if (user) {
        useAuth.setState({ user: { ...user, xp: r.total_xp } });
      }
    } catch (e: any) {
      setError(e?.message ?? "Could not mark lesson complete.");
    } finally {
      setCompleting(false);
    }
  }

  if (busy) return <ActivityIndicator style={{ flex: 1, marginTop: 40 }} color="#b73535" />;
  if (!lesson) return <Failure message={error || "Lesson not found."} retry={() => setRetry(r => r + 1)} />;

  return (
    <ScrollView style={styles.container} contentContainerStyle={ui.page}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Text style={s.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={s.levelBadge}>{lesson.hsk_level}</Text>
      </View>

      <Text style={ui.title}>{lesson.title_en}</Text>
      <Text style={ui.subtitle}>{lesson.title_zh} · {lesson.topic}</Text>

      {/* Lesson info */}
      <View style={ui.card}>
        <Text style={s.sectionTitle}>📋 Info</Text>
        <Text style={s.notes}>Book: {lesson.book} · Volume {lesson.volume} · Lesson {lesson.lesson_number}</Text>
      </View>

      {/* Audio tracks */}
      {lesson.audio_tracks && lesson.audio_tracks.length > 0 && (
        <View style={ui.card}>
          <Text style={s.sectionTitle}>🔊 Audio</Text>
          {lesson.audio_tracks.map((t, i) => (
            <View key={i} style={s.audioItem}>
              <Text style={s.audioLabel}>{t.label ?? t.section ?? `Track ${i + 1}`}</Text>
              <Text style={s.audioUrl}>{t.track}</Text>
            </View>
          ))}
        </View>
      )}

      {!!error && <Failure message={error} retry={() => setError("")} />}

      {/* Complete button / result */}
      {result ? (
        <View style={[ui.card, s.resultCard]}>
          <Text style={s.resultEmoji}>{result.already_completed ? "✅" : "🎉"}</Text>
          <Text style={s.resultTitle}>
            {result.already_completed ? "Already completed!" : "Lesson complete!"}
          </Text>
          {!result.already_completed && (
            <Text style={s.xpText}>+{result.xp_earned} XP · Total: {result.total_xp} XP</Text>
          )}
          <TouchableOpacity style={s.doneBtn} onPress={() => router.back()}>
            <Text style={s.doneBtnText}>← Back to course</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity style={s.completeBtn} onPress={complete} disabled={completing}>
          {completing
            ? <ActivityIndicator color="#fff" />
            : <Text style={s.completeBtnText}>✅ Mark as complete · +20 XP</Text>
          }
        </TouchableOpacity>
      )}
    </ScrollView>
  );
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
  sectionTitle: { fontSize: 16, fontWeight: "700", color: "#263d35", marginBottom: 8 },
  vocabRow: { flexDirection: "row", alignItems: "center", gap: 16, paddingVertical: 8 },
  vocabDivider: { borderTopWidth: 1, borderTopColor: "#f0ece5" },
  hanzi: { fontSize: 28, color: "#263d35", width: 64 },
  vocabMeta: { flex: 1, gap: 2 },
  pinyin: { fontSize: 14, color: "#a63232" },
  meaning: { fontSize: 14, color: "#545f59" },
  notes: { fontSize: 15, color: "#545f59", lineHeight: 24 },
  audioItem: { paddingVertical: 6 },
  audioLabel: { fontSize: 14, fontWeight: "600", color: "#263d35" },
  audioUrl: { fontSize: 12, color: "#888" },
  completeBtn: {
    backgroundColor: "#3a9e6b", borderRadius: 16, padding: 18, alignItems: "center",
  },
  completeBtnText: { color: "#fff", fontSize: 17, fontWeight: "700" },
  resultCard: { alignItems: "center", gap: 8 },
  resultEmoji: { fontSize: 40 },
  resultTitle: { fontSize: 20, fontWeight: "700", color: "#263d35" },
  xpText: { fontSize: 16, color: "#3a9e6b", fontWeight: "600" },
  doneBtn: { backgroundColor: "#b73535", borderRadius: 12, paddingHorizontal: 24, paddingVertical: 12, marginTop: 4 },
  doneBtnText: { color: "#fff", fontWeight: "700" },
});

import React, { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  View,
} from "react-native";
import { router } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";
import { useContent } from "../hooks/useContent";
import { api } from "../hooks/useAuth";
import { Failure, Levels, ui } from "../components/StudyUI";
import type { ReadingSummary, ReadingStatsResponse } from "../services/contracts";

// ─── small progress bar ──────────────────────────────────────────────────────
function ProgressBar({ pct, color = "#4CAF50" }: { pct: number; color?: string }) {
  return (
    <View style={{ height: 6, backgroundColor: "#e0e0e0", borderRadius: 3, overflow: "hidden" }}>
      <View style={{ width: `${Math.min(100, pct)}%`, height: "100%", backgroundColor: color, borderRadius: 3 }} />
    </View>
  );
}

// ─── stats card row ──────────────────────────────────────────────────────────
function StatsCard({ stats }: { stats: ReadingStatsResponse }) {
  const { total_completed, total_texts, levels } = stats;
  const overall = total_texts > 0 ? (total_completed / total_texts) * 100 : 0;
  return (
    <View style={[ui.card, { marginBottom: 12 }]}>
      <Text style={[ui.pinyin, { marginBottom: 4 }]}>Your progress</Text>
      <Text style={{ marginBottom: 6 }}>
        {total_completed}/{total_texts} stories read
      </Text>
      <ProgressBar pct={overall} />
      <View style={[ui.row, { flexWrap: "wrap", marginTop: 10, gap: 8 }]}>
        {levels.map((lvl) => (
          <View key={lvl.hsk_level} style={{ minWidth: 90, flex: 1 }}>
            <Text style={{ fontSize: 11, color: "#555", marginBottom: 2 }}>
              {lvl.hsk_level}
            </Text>
            <ProgressBar pct={lvl.pct} color={lvl.pct >= 100 ? "#4CAF50" : "#2196F3"} />
            <Text style={{ fontSize: 10, color: "#888", marginTop: 2 }}>
              {lvl.completed}/{lvl.total}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

// ─── main screen ─────────────────────────────────────────────────────────────
export default function ReadingScreen() {
  const [level, setLevel] = useState("HSK1");
  const [topic, setTopic] = useState<string | null>(null);
  const [stats, setStats] = useState<ReadingStatsResponse | null>(null);

  const { data, loading, error, reload } = useContent<ReadingSummary[]>(
    `/reading/texts?hsk_level=${level}`
  );

  // Reload stats when screen is focused
  useFocusEffect(
    React.useCallback(() => {
      let active = true;
      api<ReadingStatsResponse>("/reading/stats")
        .then((s) => { if (active) setStats(s); })
        .catch(() => {/* non-fatal */});
      return () => { active = false; };
    }, [])
  );

  const topics = Array.from(new Set(data?.map((item) => item.topic) ?? []));
  const visible = data?.filter((item) => !topic || item.topic === topic) ?? [];

  return (
    <ScrollView contentContainerStyle={ui.page}>
      <Text style={ui.title}>Reading Library</Text>
      <Text style={ui.subtitle}>
        Read graded passages with pinyin and English support.
      </Text>

      {/* Stats block */}
      {stats && <StatsCard stats={stats} />}

      {/* Level selector */}
      <Levels
        value={level}
        onChange={(value) => {
          setLevel(value);
          setTopic(null);
        }}
      />

      {/* Topic filter chips */}
      {loading ? (
        <ActivityIndicator accessibilityLabel="Loading reading library" />
      ) : error ? (
        <Failure message={error} retry={reload} />
      ) : (
        <>
          {!!data?.length && (
            <View style={ui.row}>
              {[null, ...topics].map((value) => (
                <Pressable
                  key={value ?? "all"}
                  accessibilityRole="button"
                  aria-pressed={topic === value}
                  onPress={() => setTopic(value)}
                  style={[ui.chip, topic === value && ui.selected]}
                >
                  <Text>{value ?? "All topics"}</Text>
                </Pressable>
              ))}
            </View>
          )}

          {!visible.length && (
            <Text>
              No reading texts available for {level} yet. Try another level or
              check back later.
            </Text>
          )}

          {visible.map((item) => (
            <Pressable
              key={item.id}
              accessibilityRole="button"
              accessibilityLabel={`Read ${item.title}`}
              style={[ui.card, item.completed && { borderLeftWidth: 4, borderLeftColor: "#4CAF50" }]}
              onPress={() =>
                router.push({ pathname: "/reading/[id]", params: { id: item.id } })
              }
            >
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1 }}>
                  <Text style={ui.pinyin}>{item.title}</Text>
                  <Text style={{ color: "#666", fontSize: 13 }}>{item.title_pinyin}</Text>
                  <Text style={{ color: "#888", fontSize: 12, marginTop: 2 }}>
                    {item.hsk_level} · {item.topic} · {item.word_count} words
                  </Text>
                </View>
                <Text style={{ fontSize: 20 }}>{item.completed ? "✅" : "→"}</Text>
              </View>
            </Pressable>
          ))}
        </>
      )}
    </ScrollView>
  );
}

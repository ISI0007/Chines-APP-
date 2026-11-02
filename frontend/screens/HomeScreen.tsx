import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { useAuth } from "../hooks/useAuth";
import { router } from "expo-router";

const MODULES = [
  { id: "flashcards",  label: "Flashcards",  emoji: "🃏", route: "/flashcards"  },
  { id: "reading",     label: "Reading",     emoji: "📖", route: "/reading"     },
  { id: "listening",   label: "Listening",   emoji: "🎧", route: "/listening"   },
  { id: "writing",     label: "Writing",     emoji: "✍️", route: "/writing"     },
  { id: "tests",       label: "HSK Tests",   emoji: "📝", route: "/tests"       },
  { id: "grammar",     label: "Grammar",     emoji: "📚", route: "/grammar"     },
  { id: "speaking",    label: "Speaking",    emoji: "🎤", route: "/speaking"    },
  { id: "course",      label: "Course",      emoji: "🏫", route: "/course"      },
  { id: "progression", label: "Progression", emoji: "📈", route: "/progression" },
];

export default function HomeScreen() {
  const { user, logout } = useAuth();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>你好, {user?.username}! 👋</Text>
          <Text style={styles.level}>{user?.hsk_level} · {user?.xp} XP</Text>
        </View>
        <View style={{ flexDirection: "row", gap: 16, alignItems: "center" }}>
          <TouchableOpacity onPress={() => router.push("/profile")}>
            <Text style={styles.logout}>👤</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={logout}>
            <Text style={styles.logout}>Logout</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Daily Goal */}
      <View style={styles.goalCard}>
        <Text style={styles.goalTitle}>Daily Goal</Text>
        <Text style={styles.goalSub}>Make time for a few words today.</Text>
      </View>

      {/* Modules Grid */}
      <Text style={styles.sectionTitle}>Study Modules</Text>
      <View style={styles.grid}>
        {MODULES.map((m) => (
          <TouchableOpacity
            key={m.id}
            style={styles.moduleCard}
            onPress={() => router.push(m.route as any)}
          >
            <Text style={styles.moduleEmoji}>{m.emoji}</Text>
            <Text style={styles.moduleLabel}>{m.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <TouchableOpacity style={styles.goalCard} onPress={() => router.push("/vocabulary")}><Text style={styles.goalTitle}>Browse vocabulary</Text></TouchableOpacity>
      <TouchableOpacity style={styles.goalCard} onPress={() => router.push("/progress")}><Text style={styles.goalTitle}>Your progress</Text></TouchableOpacity>
      <TouchableOpacity style={[styles.goalCard, { backgroundColor: "#42745b" }]} onPress={() => router.push("/leaderboard")}><Text style={styles.goalTitle}>🏆 Leaderboard</Text></TouchableOpacity>
      <TouchableOpacity onPress={() => router.push("/about")}><Text style={styles.logout}>About and data sources</Text></TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9f9f9" },
  content: { padding: 20 },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 },
  greeting: { fontSize: 22, fontWeight: "700", color: "#111" },
  level: { fontSize: 13, color: "#666", marginTop: 2 },
  logout: { color: "#E53935", fontSize: 14 },
  goalCard: {
    backgroundColor: "#E53935", borderRadius: 14, padding: 18, marginBottom: 24,
  },
  goalTitle: { color: "#fff", fontWeight: "700", fontSize: 16 },
  goalSub: { color: "rgba(255,255,255,0.85)", fontSize: 13, marginTop: 4 },
  sectionTitle: { fontSize: 18, fontWeight: "700", marginBottom: 14, color: "#111" },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  moduleCard: {
    width: "47%", backgroundColor: "#fff", borderRadius: 14,
    padding: 20, alignItems: "center",
    shadowColor: "#000", shadowOpacity: 0.06, shadowRadius: 8, elevation: 2,
  },
  moduleEmoji: { fontSize: 32, marginBottom: 8 },
  moduleLabel: { fontSize: 14, fontWeight: "600", color: "#333" },
});

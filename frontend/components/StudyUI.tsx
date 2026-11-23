import React from "react";
import { ActivityIndicator, Button, Pressable, StyleSheet, Text, View } from "react-native";
import { Redirect } from "expo-router";
import { useAuth } from "../hooks/useAuth";
export function Protected({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <ActivityIndicator accessibilityLabel="Restoring session" />;
  return user ? <>{children}</> : <Redirect href="/login" />;
}
export function Levels({ value, onChange, disabled = false }: { value: string; onChange(value: string): void; disabled?: boolean }) {
  const levels = ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6", "HSK7-9"];
  return <View style={ui.row}>{levels.map(level => <Pressable key={level} disabled={disabled} accessibilityRole="button" accessibilityState={{ selected: value === level, disabled }} onPress={() => onChange(level)} style={[ui.chip, value === level && ui.selected]}><Text style={[ui.chipText, value === level && ui.selectedText]}>{level === "HSK7-9" ? "HSK 7–9" : `HSK ${level.slice(3)}`}</Text></Pressable>)}</View>;
}
export function Failure({ message, retry }: { message: string; retry(): void }) {
  return <View style={ui.card}><Text accessibilityRole="alert">{message}</Text><Button title="Try again" onPress={retry} color="#b73535" /></View>;
}
export const ui = StyleSheet.create({
  page: { padding: 20, gap: 17, maxWidth: 760, width: "100%", alignSelf: "center", paddingBottom: 56, backgroundColor: "#f7f6f2" },
  title: { fontSize: 28, fontWeight: "800", color: "#263b30", letterSpacing: -0.5 },
  subtitle: { fontSize: 15, color: "#737C74", lineHeight: 23 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 9, alignItems: "center" },
  chip: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 13, backgroundColor: "#eeece5", borderWidth: 1, borderColor: "#eeece5" }, selected: { backgroundColor: "#294e3c", borderColor: "#294e3c" }, chipText: { color: "#555e56", fontSize: 13, fontWeight: "600" }, selectedText: { color: "#fff" },
  card: { padding: 20, gap: 14, borderRadius: 20, backgroundColor: "#fff", borderWidth: 1, borderColor: "#e9e7e0", shadowColor: "#193b35", shadowOpacity: 0.035, shadowRadius: 9, elevation: 1 },
  hanzi: { fontSize: 46, color: "#263b30" }, pinyin: { fontSize: 20, color: "#ad5548" },
});

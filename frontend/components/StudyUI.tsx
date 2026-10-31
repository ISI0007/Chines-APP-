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
  return <View style={ui.row}>{[1,2,3,4,5,6].map(n => <Pressable key={n} disabled={disabled} accessibilityRole="button" accessibilityState={{ selected: value === `HSK${n}`, disabled }} onPress={() => onChange(`HSK${n}`)} style={[ui.chip, value === `HSK${n}` && ui.selected]}><Text>HSK {n}</Text></Pressable>)}</View>;
}
export function Failure({ message, retry }: { message: string; retry(): void }) {
  return <View style={ui.card}><Text accessibilityRole="alert">{message}</Text><Button title="Try again" onPress={retry} color="#b73535" /></View>;
}
export const ui = StyleSheet.create({
  page: { padding: 24, gap: 20, maxWidth: 800, width: "100%", alignSelf: "center", paddingBottom: 48 },
  title: { fontSize: 28, fontWeight: "700", color: "#263d35" },
  subtitle: { fontSize: 16, color: "#545f59", lineHeight: 24 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 12, alignItems: "center" },
  chip: { padding: 12, borderRadius: 12, backgroundColor: "#eee7df" }, selected: { backgroundColor: "#b9d8c8" },
  card: { padding: 24, gap: 14, borderRadius: 20, backgroundColor: "#fff", borderWidth: 1, borderColor: "#e2ddd3" },
  hanzi: { fontSize: 48, color: "#263d35" }, pinyin: { fontSize: 22, color: "#a63232" },
});

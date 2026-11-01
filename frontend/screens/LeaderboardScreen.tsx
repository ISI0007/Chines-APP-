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
import { api, useAuth } from "../hooks/useAuth";
import { Failure, ui } from "../components/StudyUI";
import type { LeaderboardEntry, LeaderboardResponse } from "../services/contracts";

const MEDAL: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

function Row({
  entry,
  isMe,
  separator,
}: {
  entry: LeaderboardEntry;
  isMe: boolean;
  separator?: boolean;
}) {
  return (
    <>
      {separator && (
        <View style={s.separator}>
          <Text style={s.separatorText}>· · ·</Text>
        </View>
      )}
      <View style={[s.row, isMe && s.rowMe]}>
        <Text style={s.rank}>{MEDAL[entry.rank] ?? `#${entry.rank}`}</Text>
        <View style={s.info}>
          <Text style={[s.username, isMe && s.usernameMe]} numberOfLines={1}>
            {entry.username}
            {isMe ? " (you)" : ""}
          </Text>
          <Text style={s.meta}>
            {entry.hsk_level} · {entry.streak_days}🔥
          </Text>
        </View>
        <Text style={[s.xp, isMe && s.xpMe]}>{entry.xp.toLocaleString()} XP</Text>
      </View>
    </>
  );
}

export default function LeaderboardScreen() {
  const currentUser = useAuth((st) => st.user);
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useFocusEffect(
    useCallback(() => {
      const controller = new AbortController();
      setBusy(true);
      setError("");
      api<LeaderboardResponse>("/users/leaderboard?limit=20", {
        signal: controller.signal,
      })
        .then((res) => {
          if (!controller.signal.aborted) setData(res);
        })
        .catch(() => {
          if (!controller.signal.aborted)
            setError("Could not load leaderboard.");
        })
        .finally(() => {
          if (!controller.signal.aborted) setBusy(false);
        });
      return () => controller.abort();
    }, [retry])
  );

  return (
    <ScrollView contentContainerStyle={ui.page}>
      <Text style={ui.title}>Leaderboard 🏆</Text>
      <Text style={s.subtitle}>Top learners by XP this week</Text>

      {busy ? (
        <ActivityIndicator accessibilityLabel="Loading leaderboard" style={{ marginTop: 40 }} />
      ) : error ? (
        <Failure message={error} retry={() => setRetry((n) => n + 1)} />
      ) : data ? (
        <>
          {data.top.map((entry) => (
            <Row
              key={entry.user_id}
              entry={entry}
              isMe={entry.user_id === currentUser?.id}
            />
          ))}

          {/* Current user outside top-20 */}
          {data.me && (
            <Row entry={data.me} isMe separator />
          )}

          <TouchableOpacity
            style={s.refreshBtn}
            onPress={() => setRetry((n) => n + 1)}
          >
            <Text style={s.refreshText}>Refresh</Text>
          </TouchableOpacity>
        </>
      ) : null}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  subtitle: {
    color: "#888",
    fontSize: 13,
    marginBottom: 20,
    textAlign: "center",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 1,
  },
  rowMe: {
    borderWidth: 2,
    borderColor: "#b73535",
    backgroundColor: "#fff5f5",
  },
  rank: {
    width: 40,
    fontSize: 20,
    textAlign: "center",
  },
  info: {
    flex: 1,
    marginLeft: 10,
  },
  username: {
    fontWeight: "700",
    fontSize: 15,
    color: "#111",
  },
  usernameMe: { color: "#b73535" },
  meta: { fontSize: 12, color: "#888", marginTop: 2 },
  xp: {
    fontWeight: "700",
    fontSize: 14,
    color: "#42745b",
    minWidth: 70,
    textAlign: "right",
  },
  xpMe: { color: "#b73535" },
  separator: {
    alignItems: "center",
    paddingVertical: 8,
  },
  separatorText: { color: "#bbb", fontSize: 16, letterSpacing: 6 },
  refreshBtn: {
    marginTop: 16,
    alignSelf: "center",
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: "#b73535",
  },
  refreshText: { color: "#fff", fontWeight: "600" },
});

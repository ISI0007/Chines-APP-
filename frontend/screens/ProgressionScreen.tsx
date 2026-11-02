import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api } from "../hooks/useAuth";
import { Failure, ui } from "../components/StudyUI";
import type { BandStatus, HskBand, ProgressionResponse } from "../services/contracts";

const STATUS_META: Record<BandStatus, { emoji: string; label: string; color: string }> = {
  locked:      { emoji: "🔒", label: "Locked",      color: "#bbb" },
  in_progress: { emoji: "📖", label: "In progress", color: "#e8a020" },
  completed:   { emoji: "✅", label: "Completed",   color: "#3a9e6b" },
};

function BandCard({ band, isCurrent }: { band: HskBand; isCurrent: boolean }) {
  const meta = STATUS_META[band.status] ?? STATUS_META.locked;
  const pct = band.threshold > 0
    ? Math.min(100, Math.round((band.mastered_count / band.threshold) * 100))
    : 0;

  return (
    <View style={[s.bandCard, isCurrent && s.bandCardCurrent]}>
      {isCurrent && <View style={s.currentBadge}><Text style={s.currentBadgeText}>CURRENT</Text></View>}
      <View style={s.bandRow}>
        <Text style={s.bandEmoji}>{meta.emoji}</Text>
        <View style={s.bandInfo}>
          <Text style={s.bandName}>Band {band.band} · {band.label}</Text>
          <Text style={s.bandMeta}>
            {band.mastered_count.toLocaleString()} / {band.threshold.toLocaleString()} words mastered
          </Text>
        </View>
        <Text style={[s.statusLabel, { color: meta.color }]}>{meta.label}</Text>
      </View>

      {/* Progress bar */}
      <View style={s.barBg}>
        <View style={[s.barFill, { width: `${pct}%` as any, backgroundColor: meta.color }]} />
      </View>
      <Text style={s.pctLabel}>{pct}%</Text>
    </View>
  );
}

export default function ProgressionScreen() {
  const [data, setData] = useState<ProgressionResponse | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useFocusEffect(useCallback(() => {
    setBusy(true); setError("");
    const controller = new AbortController();
    api<ProgressionResponse>("/progression", { signal: controller.signal })
      .then(r => { if (!controller.signal.aborted) setData(r); })
      .catch(() => { if (!controller.signal.aborted) setError("Could not load progression data."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [retry]));

  const currentBand = data?.bands.find(b => b.band === data.current_band);

  return (
    <ScrollView style={styles.container} contentContainerStyle={ui.page}>
      <Text style={ui.title}>📈 HSK Progression</Text>
      <Text style={ui.subtitle}>Your nine-band journey through HSK 3.0</Text>

      {busy && <ActivityIndicator color="#b73535" style={{ marginTop: 20 }} />}
      {!!error && <Failure message={error} retry={() => setRetry(r => r + 1)} />}

      {/* Current band summary */}
      {currentBand && (
        <View style={[ui.card, s.currentSummary]}>
          <Text style={s.currentTitle}>You are on Band {data!.current_band}</Text>
          <Text style={s.currentSub}>{currentBand.label}</Text>
          <Text style={s.currentWords}>
            {currentBand.mastered_count.toLocaleString()} / {currentBand.threshold.toLocaleString()} words mastered
          </Text>
          {/* Overall bar */}
          <View style={s.barBg}>
            <View style={[s.barFill, {
              width: `${Math.min(100, Math.round(currentBand.mastered_count / currentBand.threshold * 100))}%` as any,
              backgroundColor: "#b73535",
            }]} />
          </View>
        </View>
      )}

      {/* All bands */}
      {data?.bands.map(band => (
        <BandCard
          key={band.band}
          band={band}
          isCurrent={band.band === data.current_band}
        />
      ))}

      {!busy && !error && !data && (
        <View style={ui.card}><Text style={{ color: "#545f59" }}>No progression data yet. Complete some vocabulary reviews to start!</Text></View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { flex: 1, backgroundColor: "#faf8f4" } });
const s = StyleSheet.create({
  bandCard: {
    backgroundColor: "#fff", borderRadius: 16, padding: 16, gap: 8,
    borderWidth: 1, borderColor: "#e2ddd3",
  },
  bandCardCurrent: { borderColor: "#b73535", borderWidth: 2, backgroundColor: "#fff8f8" },
  currentBadge: {
    alignSelf: "flex-start", backgroundColor: "#b73535",
    borderRadius: 8, paddingHorizontal: 10, paddingVertical: 3,
  },
  currentBadgeText: { color: "#fff", fontSize: 11, fontWeight: "800", letterSpacing: 1 },
  bandRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  bandEmoji: { fontSize: 24, width: 36, textAlign: "center" },
  bandInfo: { flex: 1, gap: 2 },
  bandName: { fontSize: 15, fontWeight: "700", color: "#263d35" },
  bandMeta: { fontSize: 13, color: "#545f59" },
  statusLabel: { fontSize: 13, fontWeight: "600" },
  barBg: { height: 8, borderRadius: 4, backgroundColor: "#eee7df", overflow: "hidden" },
  barFill: { height: 8, borderRadius: 4 },
  pctLabel: { fontSize: 12, color: "#888", textAlign: "right" },
  currentSummary: { alignItems: "center", gap: 6, paddingVertical: 24 },
  currentTitle: { fontSize: 22, fontWeight: "800", color: "#263d35" },
  currentSub: { fontSize: 16, color: "#545f59" },
  currentWords: { fontSize: 15, color: "#3a9e6b", fontWeight: "600" },
});

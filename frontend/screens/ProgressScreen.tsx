import React, { useCallback, useState } from "react";
import { ActivityIndicator, Button, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api, useAuth } from "../hooks/useAuth";
import { Failure, ui } from "../components/StudyUI";
import type { Progress } from "../services/contracts";

type LearnerReport = {
  user: { id: number; email: string; username: string; hsk_level: string; xp: number; streak_days: number; created_at: string };
  levels: Record<string, { words_reviewed: number; words_learned: number; words_due: number; characters_practiced: number; characters_mastered: number }>;
  activity: { reading_completed: number; reading_available: number; grammar_completed: number; grammar_available: number; tests_completed: number; test_average_percent: number | null; test_history: Array<{ level: string; score_percent: number; correct_answers: number; total_questions: number; passed: boolean; finished_at: string | null }> };
};

export default function ProgressScreen() {
  const [data, setData] = useState<Progress | null>(null);
  const [report, setReport] = useState<LearnerReport | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useFocusEffect(useCallback(() => {
    const controller = new AbortController(); setBusy(true); setError("");
    Promise.all([
      api<Progress>("/vocabulary/progress", { signal: controller.signal }),
      api<LearnerReport>("/users/me/report", { signal: controller.signal }),
    ]).then(([progress, learnerReport]) => {
      if (controller.signal.aborted) return;
      setData(progress); setReport(learnerReport);
      const user = useAuth.getState().user;
      if (user) useAuth.setState({ user: { ...user, xp: progress.user_xp, streak_days: progress.streak_days } });
    }).catch(() => { if (!controller.signal.aborted) setError("Could not load your learning report."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [retry]));

  const totalLearned = data ? Object.values(data.levels).reduce((sum, level) => sum + level.learned, 0) : 0;
  const rank = data && data.user_xp >= 5000 ? "Fluent" : data && data.user_xp >= 1500 ? "Advanced" : data && data.user_xp >= 500 ? "Intermediate" : "Beginner";
  const rankSteps = ["Beginner", "Intermediate", "Advanced", "Fluent"];
  return <ScrollView contentContainerStyle={s.page}>
    <Text style={s.kicker}>YOUR JOURNEY · 学习记录</Text><Text style={ui.title}>Your learning report</Text>
    {busy ? <ActivityIndicator accessibilityLabel="Loading progress" /> : error ? <Failure message={error} retry={() => setRetry(n => n + 1)} /> : data && report && <>
      <View style={s.hero}>
        <View style={s.identity}><View style={s.avatar}><Text style={s.avatarText}>{report.user.username.slice(0, 1).toUpperCase()}</Text></View><View style={{ flexShrink: 1 }}><Text style={s.name}>{report.user.username}</Text><Text style={s.email}>{report.user.email}</Text><Text style={s.rank}>{rank} learner · current level {report.user.hsk_level}</Text></View></View>
        <View style={s.stats}><View><Text style={s.statNum}>{data.user_xp}</Text><Text style={s.statLabel}>TOTAL XP</Text></View><View><Text style={s.statNum}>{totalLearned}</Text><Text style={s.statLabel}>WORDS LEARNED</Text></View><View><Text style={s.statNum}>{data.streak_days}🔥</Text><Text style={s.statLabel}>DAY STREAK</Text></View></View>
        <View style={s.rankTrack}>{rankSteps.map((step, i) => <View key={step} style={[s.rankDot, i <= rankSteps.indexOf(rank) && s.rankDotOn]} />)}</View>
        <Text style={s.rankCaption}>Account #{report.user.id} · Member since {new Date(report.user.created_at).toLocaleDateString()}</Text>
      </View>
      <View style={ui.card}><Text style={s.sectionTitle}>Activity summary</Text>
        <Text>Reading completed: {report.activity.reading_completed} of {report.activity.reading_available}</Text>
        <Text>Grammar lessons completed: {report.activity.grammar_completed} of {report.activity.grammar_available}</Text>
        <Text>HSK tests completed: {report.activity.tests_completed}{report.activity.test_average_percent !== null ? ` · recent average ${report.activity.test_average_percent}%` : ""}</Text>
        <Text>Words reviewed: {Object.values(report.levels).reduce((n, level) => n + level.words_reviewed, 0)}</Text>
        <Text>Chinese characters mastered: {Object.values(report.levels).reduce((n, level) => n + level.characters_mastered, 0)}</Text>
      </View>
      {report.activity.test_history.length > 0 && <View style={ui.card}><Text style={s.sectionTitle}>Recent test results</Text>{report.activity.test_history.map((test, i) => <Text key={`${test.finished_at}-${i}`}>{test.level} · {test.score_percent}% · {test.correct_answers}/{test.total_questions} correct · {test.passed ? "Passed" : "Keep practicing"}</Text>)}</View>}
      <View style={s.section}><Text style={s.sectionTitle}>Vocabulary by HSK level</Text><Text style={s.sectionSub}>Words you’ve learned and activity on each level</Text></View>
      <Text style={s.note}>Each level counts words introduced at that level, not cumulative totals.</Text>
      {Object.entries(data.levels).sort(([a], [b]) => a.localeCompare(b)).map(([level, progress]) => {
        const percent = progress.total ? Math.min(100, progress.learned / progress.total * 100) : 0;
        const detail = report.levels[level];
        return <View key={level} style={s.levelCard}><View style={s.levelHead}><Text style={s.levelTitle}>{level}</Text><Text style={s.levelPercent}>{Math.round(percent)}%</Text></View><Text style={s.levelMeta}>{progress.learned} of {progress.total} words learned</Text><View accessibilityRole="progressbar" accessibilityLabel={`${level} words learned`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(percent)} style={s.track}><View style={[s.fill, { width: `${percent}%` }]} /></View><Text style={s.due}>{progress.due_for_review} words due for review</Text><Text style={s.due}>Reviewed {detail?.words_reviewed ?? 0} · characters practiced {detail?.characters_practiced ?? 0} · mastered {detail?.characters_mastered ?? 0}</Text></View>;
      })}
      <Button title="Refresh report" onPress={() => setRetry(n => n + 1)} color="#b73535" />
    </>}
  </ScrollView>;
}

const s = StyleSheet.create({ page: { ...ui.page, gap: 16 }, kicker: { fontSize: 10, fontWeight: "800", letterSpacing: 1.5, color: "#66806B" }, hero: { backgroundColor: "#234D3D", borderRadius: 22, padding: 20, gap: 18 }, identity: { flexDirection: "row", alignItems: "center", gap: 13 }, avatar: { width: 48, height: 48, borderRadius: 24, backgroundColor: "#D9E5D5", alignItems: "center", justifyContent: "center" }, avatarText: { fontSize: 20, fontWeight: "800", color: "#294e3c" }, name: { fontSize: 18, fontWeight: "800", color: "#fff" }, email: { fontSize: 11, color: "#D1DFD1", marginTop: 2 }, rank: { fontSize: 12, color: "#D1DFD1", marginTop: 3 }, stats: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 14, borderTopWidth: 1, borderBottomWidth: 1, borderColor: "#537362" }, statNum: { fontSize: 22, fontWeight: "800", color: "#fff" }, statLabel: { fontSize: 8, letterSpacing: 1, fontWeight: "800", color: "#C2D2C2", marginTop: 4 }, rankTrack: { flexDirection: "row", gap: 8 }, rankDot: { height: 5, flex: 1, borderRadius: 4, backgroundColor: "#4C6958" }, rankDotOn: { backgroundColor: "#D8C58F" }, rankCaption: { fontSize: 11, color: "#D1DFD1" }, section: { gap: 4, marginTop: 6 }, sectionTitle: { fontSize: 17, fontWeight: "800", color: "#2B342E" }, sectionSub: { fontSize: 12, color: "#777F78" }, note: { fontSize: 12, color: "#777F78" }, levelCard: { padding: 17, gap: 10, borderRadius: 17, backgroundColor: "#fff", borderWidth: 1, borderColor: "#e9e7e0" }, levelHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" }, levelTitle: { fontSize: 17, fontWeight: "800", color: "#293D31" }, levelPercent: { fontSize: 12, fontWeight: "800", color: "#56745B" }, levelMeta: { fontSize: 12, color: "#777F78" }, track: { height: 5, borderRadius: 4, backgroundColor: "#E7E5DE", overflow: "hidden" }, fill: { height: 5, backgroundColor: "#557A5D" }, due: { fontSize: 11, color: "#777F78" } });

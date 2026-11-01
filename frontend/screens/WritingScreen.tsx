/**
 * WritingScreen — stroke-order practice for HSK writing characters.
 *
 * Stroke animation is handled client-side by hanzi-writer (web) or
 * a WebView wrapper on native.  This screen owns:
 *   - fetching the character curriculum  GET /writing/characters
 *   - recording each attempt              POST /writing/characters/{id}/practice
 *   - showing per-level progress          GET /writing/progress
 *
 * On React Native we render the character glyph as a large Text element.
 * The "stroke quiz" is intentionally simple: the learner writes on paper
 * (or their own canvas app), then self-rates.  A full hanzi-writer WebView
 * integration can replace the rating buttons later without changing the API calls.
 */
import React, { useCallback, useState } from "react";
import {
  ActivityIndicator, Button, Pressable, ScrollView, Text, View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api, useAuth } from "../hooks/useAuth";
import { Failure, Levels, ui } from "../components/StudyUI";
import type { PracticeResult, WritingCharacter, WritingProgress } from "../services/contracts";

export default function WritingScreen() {
  const [level, setLevel] = useState("HSK1");
  const [chars, setChars] = useState<WritingCharacter[]>([]);
  const [progress, setProgress] = useState<WritingProgress | null>(null);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [busy, setBusy] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [earned, setEarned] = useState(0);
  const [retry, setRetry] = useState(0);

  useFocusEffect(useCallback(() => {
    let active = true;
    setBusy(true); setError(""); setChars([]); setIndex(0); setRevealed(false);
    setNotice(""); setEarned(0);

    Promise.all([
      api<WritingCharacter[]>(`/writing/characters?hsk_level=${level}`),
      api<WritingProgress>("/writing/progress"),
    ]).then(([c, p]) => {
      if (!active) return;
      setChars(c);
      setProgress(p);
    }).catch(() => {
      if (active) setError("Could not load writing curriculum.");
    }).finally(() => {
      if (active) setBusy(false);
    });

    return () => { active = false; };
  }, [level, retry]));

  const char = chars[index];
  const lp = progress?.levels[level as keyof typeof progress.levels];

  async function record(mastered: boolean) {
    if (!char || saving) return;
    setSaving(true);
    try {
      const result = await api<PracticeResult>(
        `/writing/characters/${char.id}/practice`,
        { method: "POST", body: JSON.stringify({ mastered }) },
      );
      // patch local state so the card updates immediately
      setChars(prev => prev.map(c =>
        c.id === char.id
          ? { ...c, times_practiced: result.times_practiced, mastered: result.mastered }
          : c,
      ));
      const user = useAuth.getState().user;
      if (user) useAuth.setState({ user: { ...user, xp: result.total_xp } });
      if (result.xp_gained > 0) {
        setEarned(n => n + result.xp_gained);
        setNotice(`+${result.xp_gained} XP`);
      } else {
        setNotice("");
      }
      setIndex(i => i + 1);
      setRevealed(false);
    } catch {
      setError("Could not save practice. Check your connection and try again.");
    } finally {
      setSaving(false);
    }
  }

  const unmastered = chars.filter(c => !c.mastered);

  return (
    <ScrollView contentContainerStyle={ui.page}>
      <Text style={ui.title}>Writing practice</Text>
      <Text style={ui.subtitle}>
        Write each character on paper, then rate yourself.{"\n"}
        Stroke order is enforced by the official HSK 3.0 书写字 syllabus.
      </Text>

      <Levels value={level} onChange={v => { setLevel(v); setIndex(0); setRevealed(false); }} disabled={saving} />

      {earned > 0 && (
        <View style={ui.card}>
          <Text>+{earned} XP earned this session</Text>
        </View>
      )}

      {/* Per-level summary */}
      {lp && (
        <View style={ui.card}>
          <Text style={ui.pinyin}>{level} writing</Text>
          <Text>{lp.mastered} / {lp.total} mastered · {lp.practiced} practiced</Text>
          <View
            accessibilityRole="progressbar"
            aria-valuemin={0} aria-valuemax={100}
            aria-valuenow={lp.total > 0 ? Math.round(lp.mastered / lp.total * 100) : 0}
            style={{ height: 10, borderRadius: 5, backgroundColor: "#eee7df", overflow: "hidden" }}
          >
            <View style={{
              width: lp.total > 0 ? `${lp.mastered / lp.total * 100}%` : "0%",
              height: 10, backgroundColor: "#a63232",
            }} />
          </View>
        </View>
      )}

      {busy ? (
        <ActivityIndicator accessibilityLabel="Loading characters" />
      ) : error ? (
        <Failure message={error} retry={() => setRetry(n => n + 1)} />
      ) : chars.length === 0 ? (
        <Text>No characters available for {level} yet.</Text>
      ) : index >= chars.length ? (
        <View style={ui.card}>
          <Text style={ui.title}>Session complete</Text>
          <Text>You've gone through all {chars.length} {level} characters.</Text>
          <Text>{unmastered.length} not yet mastered.</Text>
          <Button title="Restart session" onPress={() => { setIndex(0); setRevealed(false); setNotice(""); setEarned(0); }} />
        </View>
      ) : char ? (
        <View style={ui.card}>
          <Text style={{ fontSize: 14, color: "#545f59" }}>
            {index + 1} / {chars.length} · {char.mastered ? "✓ mastered" : char.times_practiced > 0 ? `practiced ${char.times_practiced}×` : "not yet practiced"}
          </Text>

          {/* The character — large enough to trace */}
          <Text style={[ui.hanzi, { fontSize: 96, textAlign: "center", letterSpacing: 8 }]}>
            {char.char}
          </Text>

          {!revealed ? (
            <Button title="Show pinyin & meaning" onPress={() => setRevealed(true)} color="#42745b" />
          ) : (
            <>
              <Text style={[ui.pinyin, { textAlign: "center" }]}>{char.pinyin}</Text>
              <Text style={{ textAlign: "center", color: "#545f59" }}>
                {char.meaning.join(" · ")}
              </Text>
              {notice ? <Text style={{ textAlign: "center", color: "#a63232" }}>{notice}</Text> : null}
              <Text style={{ textAlign: "center", color: "#545f59", fontSize: 13 }}>
                Did you write it correctly?
              </Text>
              <View style={[ui.row, { justifyContent: "center" }]}>
                <Pressable
                  style={[ui.chip, { backgroundColor: "#f5e0e0", flex: 1 }]}
                  disabled={saving}
                  onPress={() => record(false)}
                  accessibilityRole="button"
                  accessibilityLabel="I got it wrong"
                >
                  <Text style={{ textAlign: "center" }}>✗ Wrong</Text>
                </Pressable>
                <Pressable
                  style={[ui.chip, { backgroundColor: "#d4edda", flex: 1 }]}
                  disabled={saving}
                  onPress={() => record(true)}
                  accessibilityRole="button"
                  accessibilityLabel="I got it right"
                >
                  <Text style={{ textAlign: "center" }}>✓ Correct</Text>
                </Pressable>
              </View>
            </>
          )}

          <View style={ui.row}>
            <Button
              title="← Previous"
              disabled={index === 0 || saving}
              onPress={() => { setIndex(i => i - 1); setRevealed(false); setNotice(""); }}
            />
            <Button
              title="Skip →"
              disabled={saving}
              onPress={() => { setIndex(i => i + 1); setRevealed(false); setNotice(""); }}
            />
          </View>
        </View>
      ) : null}

      {/* Full character list for this level */}
      <Text style={ui.pinyin}>All {level} characters</Text>
      <View style={[ui.row, { flexWrap: "wrap" }]}>
        {chars.map((c, i) => (
          <Pressable
            key={c.id}
            onPress={() => { setIndex(i); setRevealed(false); setNotice(""); }}
            accessibilityRole="button"
            accessibilityLabel={`${c.char} ${c.pinyin}`}
            style={[
              ui.chip,
              index === i && ui.selected,
              c.mastered && { backgroundColor: "#b9d8c8" },
            ]}
          >
            <Text style={ui.hanzi}>{c.char}</Text>
          </Pressable>
        ))}
      </View>
    </ScrollView>
  );
}

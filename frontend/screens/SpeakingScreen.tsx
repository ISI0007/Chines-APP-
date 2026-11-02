import React, { useCallback, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api } from "../hooks/useAuth";
import { Failure, Levels, ui } from "../components/StudyUI";
import type { ShadowingResult, ShadowingSubmitRequest } from "../services/contracts";

/** Sample sentences per level for shadowing practice */
const SENTENCES: Record<string, { text: string; pinyin: string }[]> = {
  HSK1: [
    { text: "你好", pinyin: "nǐ hǎo" },
    { text: "谢谢你", pinyin: "xiè xiè nǐ" },
    { text: "我是学生", pinyin: "wǒ shì xué shēng" },
    { text: "今天天气很好", pinyin: "jīn tiān tiān qì hěn hǎo" },
  ],
  HSK2: [
    { text: "你叫什么名字", pinyin: "nǐ jiào shén me míng zì" },
    { text: "我喜欢吃中国菜", pinyin: "wǒ xǐ huān chī zhōng guó cài" },
    { text: "现在几点了", pinyin: "xiàn zài jǐ diǎn le" },
  ],
  HSK3: [
    { text: "我需要练习说汉语", pinyin: "wǒ xū yào liàn xí shuō hàn yǔ" },
    { text: "你能帮我一下吗", pinyin: "nǐ néng bāng wǒ yī xià ma" },
  ],
  HSK4: [
    { text: "他对这件事很感兴趣", pinyin: "tā duì zhè jiàn shì hěn gǎn xìng qù" },
    { text: "我们应该保护环境", pinyin: "wǒ men yīng gāi bǎo hù huán jìng" },
  ],
  HSK5: [
    { text: "这个问题需要认真考虑", pinyin: "zhè gè wèn tí xū yào rèn zhēn kǎo lǜ" },
  ],
  HSK6: [
    { text: "文化交流有助于增进相互理解", pinyin: "wén huà jiāo liú yǒu zhù yú zēng jìn xiāng hù lǐ jiě" },
  ],
};

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? "#3a9e6b" : pct >= 60 ? "#e8a020" : "#b73535";
  return (
    <View style={s.barBg}>
      <View style={[s.barFill, { width: `${pct}%` as any, backgroundColor: color }]} />
      <Text style={[s.barLabel, { color }]}>{pct}%</Text>
    </View>
  );
}

export default function SpeakingScreen() {
  const [level, setLevel] = useState("HSK1");
  const [idx, setIdx] = useState(0);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ShadowingResult | null>(null);
  const [error, setError] = useState("");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const sentences = SENTENCES[level] ?? SENTENCES.HSK1;
  const sentence = sentences[idx % sentences.length];

  useFocusEffect(useCallback(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []));

  function nextSentence() {
    setIdx(i => i + 1);
    setResult(null);
    setError("");
  }

  function changeLevel(l: string) {
    setLevel(l);
    setIdx(0);
    setResult(null);
    setError("");
  }

  /** Simulate recording: collect a short "recording" period then submit heuristic audio */
  async function handleRecord() {
    if (recording || busy) return;
    setRecording(true);
    setResult(null);
    setError("");
    setElapsed(0);
    timerRef.current = setInterval(() => setElapsed(n => n + 1), 1000);

    // Simulate up to 3 seconds of "recording" then auto-submit
    await new Promise(r => setTimeout(r, 3000));
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setRecording(false);
    setBusy(true);

    try {
      // Send a minimal base64 payload — backend uses heuristic scoring
      const fakeAudio = btoa("audio-placeholder-" + Date.now());
      const body: ShadowingSubmitRequest = {
        audio_base64: fakeAudio,
        audio_format: "webm",
        target_text: sentence.text,
        target_pinyin: sentence.pinyin,
      };
      const r = await api<ShadowingResult>("/shadowing/submit", {
        method: "POST",
        body: JSON.stringify(body),
      });
      setResult(r);
    } catch (e: any) {
      setError(e?.message ?? "Submission failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={[ui.page]}>
      <Text style={ui.title}>🎤 Speaking Practice</Text>
      <Text style={ui.subtitle}>Read the sentence aloud, then tap Record.</Text>

      <Levels value={level} onChange={changeLevel} disabled={recording || busy} />

      {/* Sentence card */}
      <View style={[ui.card, s.sentenceCard]}>
        <Text style={ui.hanzi}>{sentence.text}</Text>
        <Text style={ui.pinyin}>{sentence.pinyin}</Text>
      </View>

      {/* Record button */}
      <TouchableOpacity
        style={[s.recordBtn, recording && s.recordBtnActive]}
        onPress={handleRecord}
        disabled={recording || busy}
        accessibilityRole="button"
        accessibilityLabel={recording ? "Recording…" : "Start recording"}
      >
        {busy ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={s.recordBtnText}>
            {recording ? `⏺ Recording… ${elapsed}s` : "⏺ Hold to record (3 s)"}
          </Text>
        )}
      </TouchableOpacity>

      {/* Error */}
      {!!error && <Failure message={error} retry={() => setError("")} />}

      {/* Result */}
      {result && (
        <View style={[ui.card, s.resultCard]}>
          <Text style={s.resultTitle}>Your score</Text>
          <ScoreBar score={result.score} />
          <Text style={s.feedback}>{result.feedback}</Text>

          {result.phoneme_breakdown && result.phoneme_breakdown.length > 0 && (
            <View style={s.phonemeRow}>
              {result.phoneme_breakdown.map((p, i) => (
                <View key={i} style={[s.phoneme, { opacity: 0.4 + p.score * 0.6 }]}>
                  <Text style={s.phonemeText}>{p.phoneme}</Text>
                  <Text style={s.phonemeScore}>{Math.round(p.score * 100)}%</Text>
                </View>
              ))}
            </View>
          )}

          <View style={ui.row}>
            <TouchableOpacity style={s.nextBtn} onPress={handleRecord}>
              <Text style={s.nextBtnText}>🔄 Retry</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[s.nextBtn, s.nextBtnGreen]} onPress={nextSentence}>
              <Text style={s.nextBtnText}>Next →</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { flex: 1, backgroundColor: "#faf8f4" } });
const s = StyleSheet.create({
  sentenceCard: { alignItems: "center", gap: 8, paddingVertical: 32 },
  recordBtn: {
    backgroundColor: "#b73535", borderRadius: 16, padding: 18, alignItems: "center",
  },
  recordBtnActive: { backgroundColor: "#7a1a1a" },
  recordBtnText: { color: "#fff", fontSize: 17, fontWeight: "600" },
  resultCard: { gap: 12 },
  resultTitle: { fontSize: 18, fontWeight: "700", color: "#263d35" },
  barBg: {
    height: 28, borderRadius: 14, backgroundColor: "#eee7df",
    overflow: "hidden", justifyContent: "center",
  },
  barFill: { position: "absolute", left: 0, top: 0, bottom: 0, borderRadius: 14 },
  barLabel: { textAlign: "center", fontWeight: "700", fontSize: 14 },
  feedback: { fontSize: 15, color: "#545f59", lineHeight: 22 },
  phonemeRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 4 },
  phoneme: {
    backgroundColor: "#eee7df", borderRadius: 10, padding: 8, alignItems: "center", minWidth: 52,
  },
  phonemeText: { fontSize: 15, fontWeight: "600", color: "#263d35" },
  phonemeScore: { fontSize: 11, color: "#545f59" },
  nextBtn: { flex: 1, backgroundColor: "#b73535", borderRadius: 12, padding: 14, alignItems: "center" },
  nextBtnGreen: { backgroundColor: "#3a9e6b" },
  nextBtnText: { color: "#fff", fontWeight: "700", fontSize: 15 },
});

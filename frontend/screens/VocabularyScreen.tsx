import React, { useEffect, useState } from "react";
import { ActivityIndicator, Button, ScrollView, Text, TextInput, View } from "react-native";
import { api } from "../hooks/useAuth";
import { Failure, Levels, ui } from "../components/StudyUI";
import { WordAudio } from "../components/WordAudio";
import type { WordPage } from "../services/contracts";
const PAGE_SIZE = 20;
export default function VocabularyScreen() {
  const [filter, setFilter] = useState({ level: "HSK1", search: "", page: 0 });
  const [query, setQuery] = useState("");
  const [data, setData] = useState<WordPage | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => setFilter(f => ({ ...f, search: query.trim(), page: 0 })), 300);
    return () => clearTimeout(timer);
  }, [query]);
  useEffect(() => {
    const controller = new AbortController();
    setBusy(true); setError(""); setData(null);
    const params = `hsk_level=${filter.level}&search=${encodeURIComponent(filter.search)}&skip=${filter.page * PAGE_SIZE}&limit=${PAGE_SIZE}`;
    api<WordPage>(`/vocabulary/words?${params}`, { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(() => { if (!controller.signal.aborted) setError("Could not load vocabulary. Check your connection and try again."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [filter, retry]);
  return <ScrollView contentContainerStyle={ui.page} keyboardShouldPersistTaps="handled">
    <Text style={ui.title}>Build your vocabulary</Text>
    <Text style={ui.subtitle}>Explore words, meanings and pronunciation at your level.</Text>
    <Text>Current library: HSK 3–6 are partial samples, not full official word lists. Pronunciation uses synthetic speech while recordings are being added.</Text>
    <Levels value={filter.level} onChange={level => setFilter(f => ({ ...f, level, page: 0 }))} />
    <TextInput accessibilityLabel="Search vocabulary" placeholder="Search Chinese, pinyin or meaning" value={query} onChangeText={setQuery} maxLength={50} autoCapitalize="none" style={[ui.card, { fontSize: 16 }]} />
    {busy ? <ActivityIndicator accessibilityLabel="Loading vocabulary" /> : error ? <Failure message={error} retry={() => setRetry(r => r + 1)} /> : <>
      <Text>{data?.total ?? 0} matching words</Text>
      {!data?.words.length && <Text>No matching words. Try another search or level.</Text>}
      {data?.words.map(word => <View key={word.id} style={ui.card}><Text style={ui.hanzi}>{word.simplified}</Text><Text style={ui.pinyin}>{word.pinyin}</Text><Text>{word.definitions.join("; ")}</Text><WordAudio word={word} /></View>)}
    </>}
    <View style={ui.row}><Button title="Previous" disabled={busy || filter.page === 0} onPress={() => setFilter(f => ({ ...f, page: f.page - 1 }))} /><Text>Page {filter.page + 1} of {Math.max(1, Math.ceil((data?.total ?? 0) / PAGE_SIZE))}</Text><Button title="Next" disabled={busy || !data || (filter.page + 1) * PAGE_SIZE >= data.total} onPress={() => setFilter(f => ({ ...f, page: f.page + 1 }))} /></View>
  </ScrollView>;
}

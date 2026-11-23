import React, { useEffect, useState } from "react";
import { ActivityIndicator, Button, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
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
    <Text style={s.kicker}>DICTIONARY · 词典</Text>
    <Text style={ui.title}>Find a word. Make it yours.</Text>
    <Text style={ui.subtitle}>Search by Chinese, pinyin, or meaning. Listen, learn, then add it to your review habit.</Text>
    <Levels value={filter.level} onChange={level => setFilter(f => ({ ...f, level, page: 0 }))} />
    <TextInput accessibilityLabel="Search vocabulary" placeholder="⌕   Chinese, pinyin, or English" value={query} onChangeText={setQuery} maxLength={50} autoCapitalize="none" style={s.search} />
    {busy ? <ActivityIndicator accessibilityLabel="Loading vocabulary" /> : error ? <Failure message={error} retry={() => setRetry(r => r + 1)} /> : <>
      <View style={s.resultHead}><Text style={s.resultLabel}>{filter.search ? "SEARCH RESULTS" : `${filter.level} · WORD LIST`}</Text><Text style={s.count}>{data?.total ?? 0}</Text></View>
      {!data?.words.length && <View style={ui.card}><Text style={s.wordMeaning}>No matching words</Text><Text style={ui.subtitle}>Try a different spelling, pinyin, or meaning.</Text></View>}
      {data?.words.map(word => <View key={word.id} style={s.wordCard}><View style={s.wordTop}><View style={s.wordCopy}><Text style={s.hanzi}>{word.simplified}</Text><Text style={s.pinyin}>{word.pinyin}</Text></View><WordAudio word={word} /></View><View style={s.divider}/><Text style={s.wordMeaning}>{word.definitions.join("; ")}</Text><Text style={s.levelTag}>{word.hsk_level} · Simplified{word.traditional !== word.simplified ? ` · Traditional ${word.traditional}` : ""}</Text></View>)}
    </>}
    <View style={s.paging}><Button title="Previous" disabled={busy || filter.page === 0} onPress={() => setFilter(f => ({ ...f, page: f.page - 1 }))} /><Text style={s.pageText}>{filter.page + 1} / {Math.max(1, Math.ceil((data?.total ?? 0) / PAGE_SIZE))}</Text><Button title="Next" disabled={busy || !data || (filter.page + 1) * PAGE_SIZE >= data.total} onPress={() => setFilter(f => ({ ...f, page: f.page + 1 }))} /></View>
    <Text style={s.note}>HSK 3.0 · Levels show where a word is introduced. Human recordings are used when a matching pronunciation is available; otherwise audio is synthetic.</Text>
  </ScrollView>;
}
const s = StyleSheet.create({kicker:{fontSize:10,fontWeight:"800",letterSpacing:1.5,color:"#66806B"},search:{backgroundColor:"#fff",borderWidth:1,borderColor:"#e6e3dc",borderRadius:15,paddingVertical:15,paddingHorizontal:16,fontSize:15,color:"#303832"},resultHead:{flexDirection:"row",justifyContent:"space-between",alignItems:"center",marginTop:3},resultLabel:{fontSize:10,fontWeight:"800",letterSpacing:1.2,color:"#7B817A"},count:{fontSize:12,fontWeight:"700",color:"#68746A"},wordCard:{backgroundColor:"#fff",borderWidth:1,borderColor:"#e9e7e0",borderRadius:19,padding:18,gap:11},wordTop:{flexDirection:"row",alignItems:"center",justifyContent:"space-between",gap:12},wordCopy:{flex:1},hanzi:{fontSize:39,color:"#293D31",fontWeight:"500"},pinyin:{fontSize:17,color:"#AD5548",marginTop:1},divider:{height:1,backgroundColor:"#F0EEE8"},wordMeaning:{fontSize:15,color:"#383E39",lineHeight:22},levelTag:{fontSize:11,color:"#82877F"},paging:{flexDirection:"row",alignItems:"center",justifyContent:"center",gap:18},pageText:{fontSize:12,color:"#737A73"},note:{fontSize:11,color:"#868A82",lineHeight:16}});

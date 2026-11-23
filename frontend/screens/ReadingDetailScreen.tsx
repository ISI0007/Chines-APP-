import React, { useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { Audio } from "expo-av";
import { Link } from "expo-router";
import { useIsFocused } from "@react-navigation/native";
import { useContent } from "../hooks/useContent";
import { Failure } from "../components/StudyUI";
import { StudyToggle } from "../components/StudyToggle";
import { CompletionButton } from "../components/CompletionButton";
import { RecordingPlayer } from "../components/RecordingPlayer";
import { API_BASE } from "../constants/api";
import { audioUrl, ttsUrl } from "../services/audio";
import type { ReadingDetail } from "../services/contracts";

type Segment = { segment: string; isWordLike?: boolean };
type SegmenterConstructor = new (locale?: string, options?: { granularity: "word" }) => { segment(value: string): Iterable<Segment> };
const Segmenter = (Intl as unknown as { Segmenter?: SegmenterConstructor }).Segmenter;
function splitParagraphs(value: string) { return value.split(/\n\s*\n/).map(part => part.trim()).filter(Boolean); }
function wordsOf(value: string) {
  if (Segmenter) return Array.from(new Segmenter("zh", { granularity: "word" }).segment(value)).map(x => x.segment);
  return Array.from(value);
}

export default function ReadingDetailScreen({ id }: { id: string }) {
  const path = /^[1-9]\d*$/.test(id) ? `/reading/texts/${id}` : null;
  const { data, setData, loading, error, reload } = useContent<ReadingDetail>(path);
  const [pinyin, setPinyin] = useState(true);
  const [translation, setTranslation] = useState(false);
  const [large, setLarge] = useState(false);
  const [activeWord, setActiveWord] = useState("");
  const wordSound = useRef<Audio.Sound | null>(null);
  const focused = useIsFocused();
  const paragraphs = useMemo(() => data ? splitParagraphs(data.content) : [], [data?.content]);
  const pinyinParagraphs = useMemo(() => data ? splitParagraphs(data.content_pinyin) : [], [data?.content_pinyin]);
  const translationParagraphs = useMemo(() => data ? splitParagraphs(data.translation) : [], [data?.translation]);
  const cover = data?.image_path ? { uri: audioUrl(API_BASE, data.image_path) } : null;

  useEffect(() => () => { void wordSound.current?.unloadAsync().catch(() => {}); wordSound.current = null; }, []);
  async function speakWord(value: string) {
    const clean = value.trim(); if (!clean || !focused) return;
    setActiveWord(clean);
    await wordSound.current?.unloadAsync().catch(() => {}); wordSound.current = null;
    try {
      const { sound } = await Audio.Sound.createAsync({ uri: ttsUrl(clean) }, { shouldPlay: true });
      wordSound.current = sound;
      sound.setOnPlaybackStatusUpdate(status => { if (status.isLoaded && status.didJustFinish) { setActiveWord(""); void sound.unloadAsync(); if (wordSound.current === sound) wordSound.current = null; } });
    } catch { setActiveWord(""); }
  }

  return <ScrollView contentContainerStyle={s.page}>
    <Link href="/reading" style={s.back}>‹  Reading shelf</Link>
    {loading ? <ActivityIndicator accessibilityLabel="Loading story" /> : error ? <Failure message={error} retry={reload} /> : data && <>
      <View style={s.headline}><Text style={s.kicker}>GRADED READER · {data.hsk_level}</Text><Text style={s.title}>{data.title}</Text><Text style={s.titlePinyin}>{data.title_pinyin}</Text><Text style={s.meta}>{data.topic}  ·  {data.word_count} words  ·  2 min</Text></View>
      {cover || data.topic === "Family" ? <View style={s.artFrame}><Image source={cover ?? require("../assets/reading-family.webp")} accessibilityLabel={data.image_description} resizeMode="cover" style={s.art}/><Text style={s.caption}>{data.image_description}</Text></View> : <View style={s.artPlaceholder}><Text style={s.artIcon}>{data.topic === "Food" ? "🍚" : data.topic === "Weather" ? "🌤️" : data.topic === "School" ? "📚" : data.topic === "Travel" ? "🚆" : "🌿"}</Text><Text style={s.caption}>{data.image_description || `A scene from ${data.topic.toLowerCase()} in everyday life.`}</Text></View>}
      <RecordingPlayer path={data.audio_path} text={data.content} />

      <View style={s.sectionHead}><Text style={s.sectionTitle}>The story</Text><Text style={s.sectionHint}>Tap a word to hear it</Text></View>
      <View style={s.controlRow}><StudyToggle label="Pinyin" value={pinyin} onChange={setPinyin} /><StudyToggle label="Translation" value={translation} onChange={setTranslation} /><StudyToggle label="Text size" value={large} onChange={setLarge} activeText="A−" inactiveText="A+" /></View>

      <View style={s.story}>{paragraphs.map((paragraph, index) => <View key={`${index}-${paragraph.slice(0,8)}`} style={s.paragraph}>
        <View style={s.wordWrap}>{wordsOf(paragraph).map((token, tokenIndex) => {
          const punctuation = /^[，。！？、；：,.!?;:]+$/.test(token);
          return <Pressable key={`${tokenIndex}-${token}`} disabled={punctuation} accessibilityRole="button" accessibilityLabel={`Hear ${token}`} onPress={() => speakWord(token)} style={[s.word, activeWord === token && s.wordActive]}><Text style={[s.hanzi,large&&s.hanziLarge]}>{token}</Text></Pressable>;
        })}</View>
        {pinyin && <Text style={s.sentencePinyin}>{pinyinParagraphs[index] || data.content_pinyin}</Text>}
        {translation && <Text style={s.sentenceTranslation}>{translationParagraphs[index] || data.translation}</Text>}
      </View>)}</View>
      {!!activeWord && <Text accessibilityLiveRegion="polite" style={s.nowPlaying}>♫  {activeWord}</Text>}
      <CompletionButton path={`${path}/complete`} completed={data.completed} label="Finish reading · +10 XP" onComplete={() => setData(value => value ? { ...value, completed: true } : value)} />
      <Text style={s.footer}>Tip: try reading the Chinese first. Turn on pinyin or translation when you want a hint.</Text>
    </>}
  </ScrollView>;
}

const s=StyleSheet.create({page:{padding:20,gap:16,maxWidth:760,width:"100%",alignSelf:"center",paddingBottom:55,backgroundColor:"#F7F6F2"},back:{fontSize:14,fontWeight:"700",color:"#58745D",paddingVertical:4},headline:{gap:5},kicker:{fontSize:10,fontWeight:"800",letterSpacing:1.35,color:"#67806A"},title:{fontSize:31,fontWeight:"800",letterSpacing:-.5,color:"#263B30",marginTop:5},titlePinyin:{fontSize:16,color:"#AD5548"},meta:{fontSize:12,color:"#7C827A",marginTop:3},artFrame:{backgroundColor:"#E8E5D8",borderRadius:19,overflow:"hidden",borderWidth:1,borderColor:"#E4E1D8"},art:{width:"100%",height:210},caption:{fontSize:11,lineHeight:16,color:"#72796F",paddingHorizontal:13,paddingVertical:10,flex:1},artPlaceholder:{minHeight:120,borderRadius:19,backgroundColor:"#E8EEE4",padding:18,flexDirection:"row",alignItems:"center",gap:14},artIcon:{fontSize:42},player:{borderRadius:16,backgroundColor:"#E9EFE5",padding:15,flexDirection:"row",alignItems:"center",marginBottom:-8},playerTitle:{fontSize:14,fontWeight:"800",color:"#304C37"},playerSub:{fontSize:11,color:"#737D70",marginTop:3},playIcon:{width:38,height:38,borderRadius:19,backgroundColor:"#315B43",alignItems:"center",justifyContent:"center"},playGlyph:{fontSize:13,color:"#fff",marginLeft:2},sectionHead:{flexDirection:"row",justifyContent:"space-between",alignItems:"baseline",marginTop:8},sectionTitle:{fontSize:20,fontWeight:"800",color:"#2B392F"},sectionHint:{fontSize:11,color:"#7B8179"},controlRow:{flexDirection:"row",flexWrap:"wrap",gap:8},story:{backgroundColor:"#fff",borderRadius:19,borderWidth:1,borderColor:"#E9E7E0",paddingHorizontal:18,paddingVertical:7},paragraph:{paddingVertical:13,borderBottomWidth:1,borderBottomColor:"#F0EFE9",gap:8},wordWrap:{flexDirection:"row",flexWrap:"wrap",alignItems:"flex-end"},word:{borderBottomWidth:1,borderBottomColor:"#D8E4D5",paddingHorizontal:1,marginRight:1},wordActive:{backgroundColor:"#F6EACD",borderBottomColor:"#B88A44"},hanzi:{fontSize:27,lineHeight:40,color:"#293D31"},hanziLarge:{fontSize:34,lineHeight:48},sentencePinyin:{fontSize:14,lineHeight:22,color:"#AD5548"},sentenceTranslation:{fontSize:13,lineHeight:20,color:"#687269"},nowPlaying:{fontSize:12,fontWeight:"700",color:"#56745A",textAlign:"center"},footer:{fontSize:11,lineHeight:16,color:"#858A82",textAlign:"center"}});

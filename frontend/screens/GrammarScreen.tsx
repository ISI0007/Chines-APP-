import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { useContent } from "../hooks/useContent";
import { Failure, Levels, ui } from "../components/StudyUI";
import type { GrammarSummary } from "../services/contracts";

export default function GrammarScreen() {
  const [level, setLevel] = useState("HSK1");
  const { data, loading, error, reload } = useContent<GrammarSummary[]>(`/grammar/lessons?hsk_level=${level}`);
  return <ScrollView contentContainerStyle={ui.page}>
    <Text style={s.kicker}>GRAMMAR · 语法</Text>
    <Text style={ui.title}>Build sentences with confidence.</Text>
    <Text style={ui.subtitle}>Learn one useful pattern, see it in context, and try making it your own.</Text>
    <Levels value={level} onChange={setLevel} />
    {loading ? <ActivityIndicator accessibilityLabel="Loading grammar library" /> : error ? <Failure message={error} retry={reload} /> : <>
      {!data?.length && <Text>{level === "HSK1" ? "No grammar lessons available yet. Check back later." : `No ${level} grammar lessons yet. Choose HSK1 to start learning.`}</Text>}
      {data?.map((item,index) => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Study ${item.title}`} style={s.lesson} onPress={() => router.push({ pathname: "/grammar/[id]", params: { id: item.id } })}>
        <View style={s.lessonHead}><Text style={s.lessonNo}>LESSON {String(index+1).padStart(2,"0")}</Text><Text style={s.lessonLevel}>{item.hsk_level}</Text></View>
        <Text style={s.lessonTitle}>{item.title}</Text><Text style={s.pattern}>{item.pattern}</Text>
        <Text style={s.open}>{item.completed ? "✓ Completed" : "Study pattern  →"}</Text>
      </Pressable>)}
    </>}
  </ScrollView>;
}
const s=StyleSheet.create({kicker:{fontSize:10,fontWeight:"800",letterSpacing:1.4,color:"#66806B"},lesson:{backgroundColor:"#fff",borderWidth:1,borderColor:"#e9e7e0",borderRadius:19,padding:18,gap:9},lessonHead:{flexDirection:"row",justifyContent:"space-between",alignItems:"center"},lessonNo:{fontSize:9,fontWeight:"800",letterSpacing:1.2,color:"#879087"},lessonLevel:{fontSize:10,fontWeight:"700",color:"#697E6A"},lessonTitle:{fontSize:21,fontWeight:"800",color:"#293D31",marginTop:3},pattern:{fontSize:14,color:"#7A8179"},open:{fontSize:12,fontWeight:"800",color:"#55745C",borderTopWidth:1,borderTopColor:"#F0EEE8",paddingTop:12,marginTop:5}});

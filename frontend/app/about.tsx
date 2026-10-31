import React from "react";
import { Linking, Pressable, ScrollView, Text } from "react-native";
import { ui } from "../components/StudyUI";

const sources = [
  { title: "ivankra/hsk30 · MIT", url: "https://github.com/ivankra/hsk30" },
  { title: "drkameleon/complete-hsk-vocabulary · MIT", url: "https://github.com/drkameleon/complete-hsk-vocabulary" },
  { title: "CC-CEDICT dictionary", url: "https://cc-cedict.org/" },
  { title: "Creative Commons Attribution-ShareAlike 4.0", url: "https://creativecommons.org/licenses/by-sa/4.0/" },
  { title: "Dataset source and licence notice", url: "https://github.com/ISI0007/Chines-APP-/blob/86917df/backend/data/hsk/NOTICE.md" },
];
export default function About() {
  return <ScrollView contentContainerStyle={ui.page}>
    <Text style={ui.title}>About this learning library</Text>
    <Text>HSK 3.0 vocabulary, levels 1–6. Levels 7–9 are not included. Different readings of the same characters are separate entries.</Text>
    <Text>Vocabulary and pinyin: ivankra/hsk30 (MIT), derived from the official syllabus, elkmovie/hsk30 and shawkynasr/HSK-official-Query-System. English meanings and frequency: drkameleon/complete-hsk-vocabulary (MIT).</Text>
    <Text>Dictionary definitions originate from CC-CEDICT and are licensed under CC BY-SA 4.0. The app dataset combines these sources, spaces pinyin by syllable, and includes manually edited meanings. Derived dictionary data remains under CC BY-SA 4.0.</Text>
    {sources.map(source => <Pressable key={source.url} accessibilityRole="link" onPress={() => { void Linking.openURL(source.url).catch(() => {}); }} style={ui.card}><Text style={{ color: "#a63232" }}>{source.title}</Text></Pressable>)}
  </ScrollView>;
}

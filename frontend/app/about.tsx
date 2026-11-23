import React from "react";
import { Linking, Pressable, ScrollView, Text } from "react-native";
import { ui } from "../components/StudyUI";

const sources = [
  { title: "ivankra/hsk30 · MIT", url: "https://github.com/ivankra/hsk30" },
  { title: "drkameleon/complete-hsk-vocabulary · MIT", url: "https://github.com/drkameleon/complete-hsk-vocabulary" },
  { title: "CC-CEDICT dictionary", url: "https://cc-cedict.org/" },
  { title: "Creative Commons Attribution-ShareAlike 4.0", url: "https://creativecommons.org/licenses/by-sa/4.0/" },
  { title: "hugolpz/audio-cmn · human Mandarin pronunciations", url: "https://github.com/hugolpz/audio-cmn" },
  { title: "Shtooka / SWAC Mandarin recording pack", url: "https://packs.shtooka.net/cmn-caen-tan/readme.txt" },
  { title: "TrainChinese Dictionary & Flashcards", url: "https://www.trainchinese.com/v2/viewApps.php?tcLanguage=en" },
  { title: "Chinese Zero To Hero · YouTube", url: "https://www.youtube.com/@ChineseZeroToHero" },
  { title: "Chinese For Us · YouTube", url: "https://www.youtube.com/@ChineseForUsOfficial" },
  { title: "Mandarin Corner · YouTube", url: "https://www.youtube.com/@MandarinCorner2" },
  { title: "Grace Mandarin Chinese · YouTube", url: "https://www.youtube.com/@GraceMandarinChinese" },
  { title: "Dataset source and licence notice", url: "https://github.com/ISI0007/Chines-APP-/blob/86917df/backend/data/hsk/NOTICE.md" },
];
export default function About() {
  return <ScrollView contentContainerStyle={ui.page}>
    <Text style={ui.title}>About this learning library</Text>
    <Text>HSK 3.0 vocabulary, levels 1–6, plus the Pleco HSK 1–9 deck. The export groups advanced cards under HSK 7–9, so the app displays these in one advanced band. Different readings of the same characters are separate entries.</Text>
    <Text>Vocabulary and pinyin: ivankra/hsk30 (MIT), derived from the official syllabus, elkmovie/hsk30 and shawkynasr/HSK-official-Query-System. English meanings and frequency: drkameleon/complete-hsk-vocabulary (MIT).</Text>
    <Text>Dictionary definitions originate from CC-CEDICT and are licensed under CC BY-SA 4.0. The app dataset combines these sources, spaces pinyin by syllable, and includes manually edited meanings. Derived dictionary data remains under CC BY-SA 4.0.</Text>
    <Text>Pleco level 1–9 definitions and card assignments were imported from a user supplied Pleco export.</Text>
    <Text>Pronunciation audio uses recordings from Yue Tan (words) and Chen Wang (syllables), curated by hugolpz/audio-cmn from Shtooka/SWAC. License: CC BY-SA. When a matching human recording is unavailable, the player uses Google synthetic speech. The audio manifest records the source and verification status of each recording.</Text>
    <Text>More listening and pronunciation lessons are linked below. Those channels provide lesson and sentence audio; their videos are not copied into single-word flashcard recordings.</Text>
    {sources.map(source => <Pressable key={source.url} accessibilityRole="link" onPress={() => { void Linking.openURL(source.url).catch(() => {}); }} style={ui.card}><Text style={{ color: "#a63232" }}>{source.title}</Text></Pressable>)}
  </ScrollView>;
}

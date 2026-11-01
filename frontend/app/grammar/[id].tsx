import React from "react";
import { useLocalSearchParams } from "expo-router";
import { Protected } from "../../components/StudyUI";
import GrammarDetailScreen from "../../screens/GrammarDetailScreen";
export default function Lesson() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <Protected><GrammarDetailScreen key={id} id={typeof id === "string" ? id : ""} /></Protected>;
}

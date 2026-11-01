import React from "react";
import { useLocalSearchParams } from "expo-router";
import { Protected } from "../../components/StudyUI";
import ReadingDetailScreen from "../../screens/ReadingDetailScreen";
export default function Story() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <Protected><ReadingDetailScreen key={id} id={typeof id === "string" ? id : ""} /></Protected>;
}

import React from "react";
import { useLocalSearchParams } from "expo-router";
import { Protected } from "../../components/StudyUI";
import LessonDetailScreen from "../../screens/LessonDetailScreen";
export default function Lesson() { const { id } = useLocalSearchParams<{ id: string }>(); return <Protected><LessonDetailScreen id={String(id ?? "")} /></Protected>; }

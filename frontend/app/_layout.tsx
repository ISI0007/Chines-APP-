import React, { useEffect } from "react";
import { Stack } from "expo-router";
import { useAuth } from "../hooks/useAuth";

export default function Layout() {
  useEffect(() => { void useAuth.getState().loadSession(); }, []);
  return <Stack screenOptions={{ headerTintColor: "#b73535", contentStyle: { backgroundColor: "#faf8f4" } }}>
    <Stack.Screen name="index" options={{ title: "学中文 · Learn Chinese" }} />
    <Stack.Screen name="login" options={{ title: "Welcome", headerBackVisible: false }} />
    <Stack.Screen name="register" options={{ title: "Create account" }} />
    <Stack.Screen name="vocabulary" options={{ title: "Vocabulary" }} />
    <Stack.Screen name="flashcards" options={{ title: "Daily review" }} />
    <Stack.Screen name="progress" options={{ title: "Your progress" }} />
    <Stack.Screen name="about" options={{ title: "About and sources" }} />
    <Stack.Screen name="tests" options={{ title: "HSK practice" }} />
    <Stack.Screen name="reading/index" options={{ title: "Reading library" }} />
    <Stack.Screen name="reading/[id]" options={{ title: "Read a story" }} />
    <Stack.Screen name="grammar/index" options={{ title: "Grammar library" }} />
    <Stack.Screen name="grammar/[id]" options={{ title: "Grammar lesson" }} />
  </Stack>;
}

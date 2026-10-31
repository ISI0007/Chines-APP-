import React from "react";
import { ActivityIndicator, View } from "react-native";
import { Redirect } from "expo-router";
import { useAuth } from "../hooks/useAuth";
import HomeScreen from "../screens/HomeScreen";

export default function Index() {
  const { user, isLoading } = useAuth();
  if (isLoading) return <View style={{ flex: 1, justifyContent: "center" }}><ActivityIndicator accessibilityLabel="Restoring session" /></View>;
  return user ? <HomeScreen /> : <Redirect href="/login" />;
}

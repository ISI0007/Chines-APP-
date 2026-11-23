import React, { useState } from "react";
import { View, Text, TextInput, Button, StyleSheet } from "react-native";
import { router } from "expo-router";
import { useAuth } from "../hooks/useAuth";
import { LANGUAGES } from "../services/languages";
import AsyncStorage from "@react-native-async-storage/async-storage";

export default function Register() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [language, setLanguage] = useState("en");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function submit() {
    if (!email.trim() || !/^[a-zA-Z0-9_]{3,30}$/.test(username) || password.length < 8) {
      setMessage("Enter an email, a username of 3–30 letters/numbers/underscores, and a password of at least 8 characters."); return;
    }
    setBusy(true); setMessage("");
    try { await useAuth.getState().register(email.trim(), username, password); router.replace("/login"); }
    catch { setMessage("Could not create the account. Check your connection or try another email and username."); }
    finally { setBusy(false); }
  }
  return <View style={styles.page}>
    <Text style={styles.title}>Start learning Chinese</Text>
    <Text>Create your account, then sign in.</Text>
    <TextInput accessibilityLabel="Email" placeholder="Email" keyboardType="email-address" autoCapitalize="none" style={styles.input} value={email} onChangeText={setEmail} />
    <TextInput accessibilityLabel="Username" placeholder="Username" autoCapitalize="none" style={styles.input} value={username} onChangeText={setUsername} />
    <TextInput accessibilityLabel="Password" placeholder="Password (8+ characters)" secureTextEntry style={styles.input} value={password} onChangeText={setPassword} />
    <Text>Learning and translation language</Text>
    <View style={styles.languages}>{LANGUAGES.map(item => <Text key={item.code} accessibilityRole="button" onPress={() => { setLanguage(item.code); void AsyncStorage.setItem("learning_language", item.code); }} style={[styles.language, language === item.code && styles.selected]}>{item.name}</Text>)}</View>
    {!!message && <Text accessibilityRole="alert">{message}</Text>}
    <Button title={busy ? "Creating account…" : "Create account"} disabled={busy} onPress={submit} color="#b73535" />
  </View>;
}
const styles = StyleSheet.create({ page: { flex: 1, padding: 24, justifyContent: "center", gap: 16, maxWidth: 520, width: "100%", alignSelf: "center" }, title: { fontSize: 28, fontWeight: "700" }, input: { padding: 16, borderWidth: 1, borderColor: "#bbb", borderRadius: 12 }, languages: { flexDirection: "row", flexWrap: "wrap", gap: 7 }, language: { overflow: "hidden", borderWidth: 1, borderColor: "#ddd", borderRadius: 10, paddingVertical: 7, paddingHorizontal: 9, color: "#555" }, selected: { backgroundColor: "#294e3c", color: "#fff", borderColor: "#294e3c" } });

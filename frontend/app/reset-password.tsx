import React, { useState } from "react";
import { ActivityIndicator, Button, StyleSheet, Text, TextInput, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { API_BASE } from "../constants/api";

export default function ResetPassword() {
  const params = useLocalSearchParams<{ token?: string }>();
  const token = typeof params.token === "string" ? params.token : "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function submit() {
    if (!token) { setError("This reset link is missing its token. Request a new link."); return; }
    if (password.length < 8) { setError("Use at least 8 characters for your new password."); return; }
    if (password !== confirm) { setError("The passwords do not match."); return; }
    setBusy(true); setError("");
    try {
      const response = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not update the password.");
      setMessage(data.message);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not contact the server."); }
    finally { setBusy(false); }
  }
  return <View style={styles.page}>
    <Text style={styles.title}>Choose a new password</Text>
    <TextInput accessibilityLabel="New password" placeholder="New password (8+ characters)" secureTextEntry autoComplete="new-password" style={styles.input} value={password} onChangeText={setPassword} />
    <TextInput accessibilityLabel="Confirm password" placeholder="Confirm new password" secureTextEntry autoComplete="new-password" style={styles.input} value={confirm} onChangeText={setConfirm} />
    {busy ? <ActivityIndicator accessibilityLabel="Updating password" /> : message ? <Button title="Go to sign in" onPress={() => router.replace("/login")} color="#b73535" /> : <Button title="Update password" onPress={submit} color="#b73535" />}
    {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
    {!!message && <Text accessibilityRole="alert">{message}</Text>}
  </View>;
}
const styles = StyleSheet.create({ page: { flex: 1, padding: 24, justifyContent: "center", gap: 16, maxWidth: 520, width: "100%", alignSelf: "center" }, title: { fontSize: 28, fontWeight: "700", color: "#263b30" }, input: { padding: 16, borderWidth: 1, borderColor: "#ccc", borderRadius: 12 }, error: { color: "#a63232" } });

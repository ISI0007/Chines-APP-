import React, { useState } from "react";
import { ActivityIndicator, Button, StyleSheet, Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { API_BASE } from "../constants/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  async function submit() {
    if (!email.trim()) { setError("Enter the email address for your account."); return; }
    setBusy(true); setError(""); setMessage(""); setToken("");
    try {
      const response = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: email.trim() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not request a password reset.");
      setMessage(data.message);
      if (data.reset_token) setToken(data.reset_token);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not contact the server."); }
    finally { setBusy(false); }
  }
  return <View style={styles.page}>
    <Text style={styles.title}>Reset your password</Text>
    <Text style={styles.copy}>Enter your account email. We’ll send a secure reset link if the account exists.</Text>
    <TextInput accessibilityLabel="Email" placeholder="Email" keyboardType="email-address" autoCapitalize="none" autoComplete="email" style={styles.input} value={email} onChangeText={setEmail} />
    {busy ? <ActivityIndicator accessibilityLabel="Sending reset instructions" /> : <Button title="Send reset instructions" onPress={submit} color="#b73535" />}
    {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
    {!!message && <Text accessibilityRole="alert">{message}</Text>}
    {!!token && <View style={styles.dev}><Text>Development reset token (use on the reset page):</Text><Text selectable>{token}</Text><Button title="Continue to reset password" onPress={() => router.push({ pathname: "/reset-password", params: { token } })} color="#b73535" /></View>}
    <Button title="Back to sign in" onPress={() => router.replace("/login")} color="#59665d" />
  </View>;
}
const styles = StyleSheet.create({ page: { flex: 1, padding: 24, justifyContent: "center", gap: 16, maxWidth: 520, width: "100%", alignSelf: "center" }, title: { fontSize: 28, fontWeight: "700", color: "#263b30" }, copy: { lineHeight: 22, color: "#59665d" }, input: { padding: 16, borderWidth: 1, borderColor: "#ccc", borderRadius: 12 }, error: { color: "#a63232" }, dev: { gap: 8, padding: 14, borderWidth: 1, borderColor: "#ddd", borderRadius: 12 } });

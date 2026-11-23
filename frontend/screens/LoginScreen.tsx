import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { useAuth } from "../hooks/useAuth";
import { router } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { LANGUAGES } from "../services/languages";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [language, setLanguage] = useState("en");
  const { login } = useAuth();

  React.useEffect(() => {
    const saved = useAuth.getState().user?.preferred_language;
    if (saved && LANGUAGES.some(item => item.code === saved)) setLanguage(saved);
    else void AsyncStorage.getItem("learning_language").then(value => { if (value && LANGUAGES.some(item => item.code === value)) setLanguage(value); });
  }, []);

  const handleLogin = async () => {
    if (!email.trim() || !password) { setError("Enter your email and password."); return; }
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.logo}>学中文</Text>
      <Text style={styles.subtitle}>Learn Chinese — HSK Ready</Text>

      <TextInput
        style={styles.input}
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />

      <Text style={{ color: "#59665d", marginBottom: 6 }}>App and question language</Text>
      <View style={styles.languages}>{LANGUAGES.map(item => <Text key={item.code} accessibilityRole="button" onPress={() => { setLanguage(item.code); void AsyncStorage.setItem("learning_language", item.code); }} style={[styles.language, language === item.code && styles.languageSelected]}>{item.name}</Text>)}</View>
      <TextInput
        style={styles.input}
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      {!!error && <Text accessibilityRole="alert" style={{ color: "#a63232", marginBottom: 12 }}>{error}</Text>}
      <TouchableOpacity style={styles.btn} onPress={handleLogin} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Log In</Text>}
      </TouchableOpacity>

      <TouchableOpacity onPress={() => router.push("/register")}>
        <Text style={styles.link}>Don't have an account? Register</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => router.push("/forgot-password")}>
        <Text style={styles.link}>Forgot your password?</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#fff" },
  logo: { fontSize: 48, textAlign: "center", marginBottom: 8, color: "#E53935" },
  subtitle: { fontSize: 16, textAlign: "center", color: "#666", marginBottom: 32 },
  input: {
    borderWidth: 1, borderColor: "#ddd", borderRadius: 10,
    padding: 14, marginBottom: 12, fontSize: 16,
  },
  btn: {
    backgroundColor: "#E53935", padding: 16, borderRadius: 10,
    alignItems: "center", marginTop: 8,
  },
  btnText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  link: { textAlign: "center", color: "#E53935", marginTop: 16 },
  languages: { flexDirection: "row", flexWrap: "wrap", gap: 7, marginBottom: 14 },
  language: { overflow: "hidden", borderWidth: 1, borderColor: "#ddd", borderRadius: 9, paddingVertical: 6, paddingHorizontal: 8, color: "#555", fontSize: 12 },
  languageSelected: { backgroundColor: "#294e3c", color: "#fff", borderColor: "#294e3c" },
});

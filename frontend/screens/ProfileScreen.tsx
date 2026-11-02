import React, { useCallback, useRef, useState } from "react";
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import * as ImagePicker from "expo-image-picker";
import { api, useAuth } from "../hooks/useAuth";
import { Failure, ui } from "../components/StudyUI";
import { API_BASE } from "../constants/api";
import type { AvatarResponse } from "../services/contracts";

const AVATAR_PLACEHOLDER = "https://ui-avatars.com/api/?background=b73535&color=fff&size=128&name=";

export default function ProfileScreen() {
  const { user } = useAuth();
  const [avatarUri, setAvatarUri] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");
  const [loadingAvatar, setLoadingAvatar] = useState(true);

  useFocusEffect(useCallback(() => {
    // Try to load existing avatar by checking the static endpoint
    if (!user) return;
    setLoadingAvatar(false);
    // Avatar URL comes from the DB — fetch profile to get it
    api<{ avatar_url?: string }>("/users/me/profile")
      .then(p => { if (p.avatar_url) setAvatarUri(p.avatar_url); })
      .catch(() => {}) // no avatar yet is fine
      .finally(() => setLoadingAvatar(false));
  }, [user]));

  async function pickAndUpload() {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      setError("Camera roll access is required to upload a photo.");
      return;
    }
    const picked = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });
    if (picked.canceled) return;

    setUploading(true);
    setError("");
    const asset = picked.assets[0];
    const ext = asset.uri.split(".").pop()?.toLowerCase() ?? "jpg";
    const mime = ext === "png" ? "image/png" : ext === "webp" ? "image/webp" : "image/jpeg";

    const form = new FormData();
    form.append("file", { uri: asset.uri, name: `avatar.${ext}`, type: mime } as any);

    try {
      const { avatar_url } = await api<AvatarResponse>("/users/me/avatar", {
        method: "POST",
        body: form,
        headers: {}, // let fetch set multipart boundary
      } as RequestInit);
      setAvatarUri(avatar_url.startsWith("http") ? avatar_url : `${API_BASE.replace("/api/v1", "")}${avatar_url}`);
    } catch (e: any) {
      setError(e?.message ?? "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function removeAvatar() {
    setDeleting(true);
    setError("");
    try {
      await api("/users/me/avatar", { method: "DELETE" });
      setAvatarUri(null);
    } catch (e: any) {
      setError(e?.message ?? "Could not remove avatar.");
    } finally {
      setDeleting(false);
    }
  }

  if (!user) return null;

  const avatarSrc = avatarUri
    ? { uri: avatarUri }
    : { uri: `${AVATAR_PLACEHOLDER}${encodeURIComponent(user.username)}` };

  return (
    <ScrollView style={styles.container} contentContainerStyle={ui.page}>
      <Text style={ui.title}>👤 Profile</Text>

      {/* Avatar */}
      <View style={s.avatarSection}>
        {loadingAvatar ? (
          <View style={s.avatarPlaceholder}><ActivityIndicator /></View>
        ) : (
          <Image source={avatarSrc} style={s.avatar} accessibilityLabel="Profile photo" />
        )}
        <View style={s.avatarButtons}>
          <TouchableOpacity style={s.btn} onPress={pickAndUpload} disabled={uploading || deleting}>
            {uploading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>📷 Change photo</Text>}
          </TouchableOpacity>
          {!!avatarUri && (
            <TouchableOpacity style={[s.btn, s.btnDanger]} onPress={removeAvatar} disabled={uploading || deleting}>
              {deleting ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>🗑 Remove</Text>}
            </TouchableOpacity>
          )}
        </View>
      </View>

      {!!error && <Failure message={error} retry={() => setError("")} />}

      {/* Stats */}
      <View style={ui.card}>
        <Text style={s.label}>Username</Text>
        <Text style={s.value}>{user.username}</Text>
      </View>

      <View style={ui.row}>
        <View style={[ui.card, s.statCard]}>
          <Text style={s.statEmoji}>🏆</Text>
          <Text style={s.statValue}>{user.xp}</Text>
          <Text style={s.statLabel}>Total XP</Text>
        </View>
        <View style={[ui.card, s.statCard]}>
          <Text style={s.statEmoji}>🔥</Text>
          <Text style={s.statValue}>{user.streak_days}</Text>
          <Text style={s.statLabel}>Day streak</Text>
        </View>
        <View style={[ui.card, s.statCard]}>
          <Text style={s.statEmoji}>📊</Text>
          <Text style={s.statValue}>{user.hsk_level}</Text>
          <Text style={s.statLabel}>Level</Text>
        </View>
      </View>

      <View style={ui.card}>
        <Text style={s.label}>Email</Text>
        <Text style={s.value}>{user.email}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { flex: 1, backgroundColor: "#faf8f4" } });
const s = StyleSheet.create({
  avatarSection: { alignItems: "center", gap: 16 },
  avatar: { width: 120, height: 120, borderRadius: 60, borderWidth: 3, borderColor: "#b73535" },
  avatarPlaceholder: {
    width: 120, height: 120, borderRadius: 60, backgroundColor: "#eee7df",
    justifyContent: "center", alignItems: "center",
  },
  avatarButtons: { flexDirection: "row", gap: 12 },
  btn: { backgroundColor: "#b73535", borderRadius: 12, paddingHorizontal: 20, paddingVertical: 12 },
  btnDanger: { backgroundColor: "#888" },
  btnText: { color: "#fff", fontWeight: "600", fontSize: 14 },
  label: { fontSize: 13, color: "#888", marginBottom: 2 },
  value: { fontSize: 17, fontWeight: "600", color: "#263d35" },
  statCard: { flex: 1, alignItems: "center", gap: 4, paddingVertical: 18 },
  statEmoji: { fontSize: 26 },
  statValue: { fontSize: 22, fontWeight: "700", color: "#263d35" },
  statLabel: { fontSize: 12, color: "#545f59" },
});

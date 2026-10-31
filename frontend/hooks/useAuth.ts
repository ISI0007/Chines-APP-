import { create } from "zustand";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { API_BASE } from "../constants/api";
import { createClient } from "../services/client";
import type { Tokens } from "../services/contracts";
interface User { id: number; email: string; username: string; hsk_level: string; xp: number; streak_days: number }
interface AuthState {
  user: User | null; accessToken: string | null; isLoading: boolean;
  login(email: string, password: string): Promise<void>;
  register(email: string, username: string, password: string): Promise<void>;
  logout(): Promise<void>; loadSession(): Promise<void>;
}
async function saveTokens(tokens: Tokens) {
  await AsyncStorage.multiSet([["access_token", tokens.access_token], ["refresh_token", tokens.refresh_token]]);
  useAuth.setState({ accessToken: tokens.access_token });
}
export const useAuth = create<AuthState>((set) => ({
  user: null, accessToken: null, isLoading: true,
  loadSession: async () => {
    try {
      const token = await AsyncStorage.getItem("access_token");
      if (token) { set({ accessToken: token }); const user = await api<User>("/auth/me"); set({ user }); }
    } catch { set({ user: null, accessToken: null }); }
    finally { set({ isLoading: false }); }
  },
  login: async (email, password) => {
    const tokens = await api<Tokens>("/auth/login", { method: "POST", body: JSON.stringify({ email: email.trim(), password }) }, false);
    await saveTokens(tokens);
    try { const user = await api<User>("/auth/me"); set({ user }); }
    catch (error) { await useAuth.getState().logout(); throw error; }
  },
  register: async (email, username, password) => {
    await api("/auth/register", { method: "POST", body: JSON.stringify({ email, username, password }) }, false);
  },
  logout: async () => {
    set({ user: null, accessToken: null });
    await AsyncStorage.multiRemove(["access_token", "refresh_token"]);
  },
}));
export const api = createClient(API_BASE, {
  access: () => useAuth.getState().accessToken,
  refresh: () => AsyncStorage.getItem("refresh_token"),
  save: saveTokens, clear: () => useAuth.getState().logout(),
});

import { create } from "zustand";
import AsyncStorage from "@react-native-async-storage/async-storage";
import axios from "axios";
import { API_BASE } from "../constants/api";

interface User {
  id: number;
  email: string;
  username: string;
  hsk_level: string;
  xp: number;
  streak_days: number;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadSession: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  isLoading: true,

  loadSession: async () => {
    const token = await AsyncStorage.getItem("access_token");
    if (token) {
      try {
        const res = await axios.get(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        set({ user: res.data, accessToken: token, isLoading: false });
      } catch {
        await AsyncStorage.removeItem("access_token");
        set({ isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },

  login: async (email, password) => {
    const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
    await AsyncStorage.setItem("access_token", res.data.access_token);
    await AsyncStorage.setItem("refresh_token", res.data.refresh_token);

    const me = await axios.get(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${res.data.access_token}` },
    });
    set({ user: me.data, accessToken: res.data.access_token });
  },

  register: async (email, username, password) => {
    await axios.post(`${API_BASE}/auth/register`, { email, username, password });
  },

  logout: async () => {
    await AsyncStorage.multiRemove(["access_token", "refresh_token"]);
    set({ user: null, accessToken: null });
  },
}));

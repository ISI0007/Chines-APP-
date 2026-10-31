import { Platform } from "react-native";

// Set this to your computer's LAN address when using a physical phone.
export const API_BASE = (process.env.EXPO_PUBLIC_API_URL ||
  (Platform.OS === "android" ? "http://10.0.2.2:8000/api/v1" : "http://localhost:8000/api/v1")).replace(/\/$/, "");

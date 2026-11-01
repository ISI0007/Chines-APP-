import { useCallback, useState } from "react";
import { useFocusEffect } from "@react-navigation/native";
import { api, useAuth } from "./useAuth";
import { ApiError } from "../services/client";

/** Reload on return from a lesson so completion badges reflect the server. */
export function useContent<T>(path: string | null) {
  const userId = useAuth(state => state.user?.id);
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useFocusEffect(useCallback(() => {
    const controller = new AbortController();
    setData(null); setError(""); setLoading(true);
    if (!path) {
      setError("This lesson link is invalid."); setLoading(false);
      return () => controller.abort();
    }
    api<T>(path, { signal: controller.signal }).then(value => {
      if (!controller.signal.aborted) setData(value);
    }).catch(error => {
      if (!controller.signal.aborted) setError(error instanceof ApiError && error.status === 404
        ? "This lesson is no longer available. Return to the library to choose another."
        : "Could not load this content. Check your connection and try again.");
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [path, userId, revision]));
  return { data, setData, loading, error, reload: () => setRevision(value => value + 1) };
}

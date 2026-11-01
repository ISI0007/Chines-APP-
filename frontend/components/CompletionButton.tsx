import React, { useEffect, useRef, useState } from "react";
import { Button, Text, View } from "react-native";
import { api, useAuth } from "../hooks/useAuth";
import type { CompletionResult } from "../services/contracts";

export function CompletionButton({ path, completed, label, onComplete }: {
  path: string; completed: boolean; label: string; onComplete(): void;
}) {
  const userId = useAuth(state => state.user?.id);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const pending = useRef(false);
  const generation = useRef(0);
  useEffect(() => {
    setSaving(false); setError(""); setMessage(""); pending.current = false;
    return () => { generation.current++; };
  }, [path, userId]);
  async function complete() {
    if (completed || pending.current) return;
    pending.current = true; setSaving(true); setError("");
    const current = generation.current;
    try {
      // Reading requires a JSON body. No comprehension score is inferred from completion.
      const result = await api<CompletionResult>(path, { method: "POST", body: JSON.stringify({}) });
      if (generation.current !== current || useAuth.getState().user?.id !== userId) return;
      const user = useAuth.getState().user;
      if (user) useAuth.setState({ user: { ...user, xp: result.total_xp } });
      onComplete();
      setMessage(result.xp_gained > 0 ? `Completed · +${result.xp_gained} XP` : "Already completed · Your progress is saved");
    } catch {
      if (generation.current === current) setError("Completion could not be confirmed. Try again; XP is awarded only for the first completion.");
    } finally {
      if (generation.current === current) { pending.current = false; setSaving(false); }
    }
  }
  return <View style={{ gap: 12 }}>
    <Button title={completed ? "Completed" : saving ? "Saving…" : error ? "Retry completion" : label} color="#a63232" disabled={saving || completed} onPress={complete} />
    {!!error && <Text accessibilityRole="alert">{error}</Text>}
    {!!message && <Text accessibilityLiveRegion="polite">{message}</Text>}
    {!completed && <Text>First completion earns 10 XP. Re-reading is always welcome.</Text>}
  </View>;
}

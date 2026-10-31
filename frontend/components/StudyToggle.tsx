import React from "react";
import { Pressable, Text } from "react-native";
import { ui } from "./StudyUI";
export function StudyToggle({ label, value, onChange, activeText, inactiveText }: {
  label: string; value: boolean; onChange(value: boolean): void; activeText?: string; inactiveText?: string;
}) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} aria-pressed={value} style={[ui.chip, value && ui.selected]} onPress={() => onChange(!value)}>
    <Text>{value ? activeText ?? `Hide ${label.toLowerCase()}` : inactiveText ?? `Show ${label.toLowerCase()}`}</Text>
  </Pressable>;
}

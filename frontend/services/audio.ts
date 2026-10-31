export function audioUrl(base: string, path: string): string {
  const root = new URL(base);
  const url = path.startsWith("/api/") ? new URL(path, root.origin) : new URL(path.replace(/^\//, ""), `${base.replace(/\/$/, "")}/`);
  if (url.origin !== root.origin) throw new Error("Audio URL must belong to the backend.");
  return url.href;
}
export function ttsUrl(text: string): string {
  return `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(text)}&tl=zh-CN&client=tw-ob`;
}

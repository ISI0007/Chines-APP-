import type { Tokens } from "./contracts";
export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
interface Session { access(): string | null; refresh(): Promise<string | null>; save(tokens: Tokens): Promise<void>; clear(): Promise<void> }
/** Coalesce concurrent refreshes; network failures are never automatically retried. */
export function createClient(base: string, session: Session, transport: typeof fetch = fetch) {
  let refreshing: Promise<void> | null = null;
  async function send(path: string, init: RequestInit = {}, authenticated = true): Promise<Response> {
    const headers = new Headers(init.headers);
    if (init.body) headers.set("Content-Type", "application/json");
    if (authenticated && session.access()) headers.set("Authorization", `Bearer ${session.access()}`);
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (init.signal?.aborted) controller.abort();
    init.signal?.addEventListener("abort", abort);
    const timer = setTimeout(abort, 15000);
    try { return await transport(`${base}${path}`, { ...init, headers, signal: controller.signal }); }
    finally { clearTimeout(timer); init.signal?.removeEventListener("abort", abort); }
  }
  async function decode<T>(response: Response): Promise<T> {
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new ApiError(response.status, typeof data?.detail === "string" ? data.detail : `Request failed (${response.status}).`);
    return data as T;
  }
  async function refresh() {
    const previous = session.access();
    const token = await session.refresh();
    if (!token) { await session.clear(); throw new ApiError(401, "Please sign in again."); }
    try {
      const tokens = await decode<Tokens>(await send("/auth/refresh", { method: "POST", body: JSON.stringify({ refresh_token: token }) }, false));
      if (session.access() !== previous) throw new ApiError(401, "Session changed. Please sign in again.");
      await session.save(tokens);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401 && session.access() === previous) await session.clear();
      throw error;
    }
  }
  return async function request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
    const originalToken = session.access();
    let response = await send(path, init, authenticated);
    if (authenticated && response.status === 401) {
      if (session.access() === originalToken) {
        if (!refreshing) refreshing = refresh().finally(() => { refreshing = null; });
        await refreshing;
      }
      if (!session.access()) throw new ApiError(401, "Please sign in again.");
      response = await send(path, init, true);
      if (response.status === 401) await session.clear();
    }
    return decode<T>(response);
  };
}

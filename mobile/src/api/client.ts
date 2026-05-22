/** 백엔드 HTTP 클라이언트.
 *
 * iOS 시뮬레이터는 localhost가 호스트로 연결되지만, 실기기/안드로이드
 * 에뮬레이터에서는 머신 IP가 필요하다. EXPO_PUBLIC_API_BASE로 덮어쓴다.
 *   예) EXPO_PUBLIC_API_BASE=http://192.168.0.10:8000
 */

export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

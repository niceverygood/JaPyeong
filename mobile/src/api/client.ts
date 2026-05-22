/** 백엔드 HTTP 클라이언트.
 *
 * 기본값:
 *  - 웹(Vercel): 같은 출처의 "/api" (서버리스 함수, CORS 불필요)
 *  - 네이티브(개발): "http://127.0.0.1:8000" (iOS 시뮬레이터는 localhost=호스트)
 * EXPO_PUBLIC_API_BASE 가 있으면 항상 우선한다.
 *   예) EXPO_PUBLIC_API_BASE=http://192.168.0.10:8000
 */

import { Platform } from "react-native";

export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE ??
  (Platform.OS === "web" ? "/api" : "http://127.0.0.1:8000");

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

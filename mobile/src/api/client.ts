/** 백엔드 HTTP 클라이언트.
 *
 * 기본값 우선순위:
 *  1. EXPO_PUBLIC_API_BASE 환경변수 (있으면 무조건)
 *     예) EXPO_PUBLIC_API_BASE=http://192.168.0.10:8000  (LAN 개발)
 *  2. 웹(Vercel): "/api" (서버리스 함수, CORS 불필요)
 *  3. 네이티브(iOS/Android): 프로덕션 https://ja-pyeong.vercel.app/api
 *     (개발 시는 EXPO_PUBLIC_API_BASE 로 LAN IP 지정)
 */

import { Platform } from "react-native";

const PROD_API = "https://ja-pyeong.vercel.app/api";

export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE ??
  (Platform.OS === "web" ? "/api" : PROD_API);

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

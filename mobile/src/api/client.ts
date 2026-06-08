/** 백엔드 HTTP 클라이언트.
 *
 * 기본값 우선순위:
 *  1. EXPO_PUBLIC_API_BASE 환경변수 (있으면 무조건)
 *     예) EXPO_PUBLIC_API_BASE=http://192.168.0.10:8000  (LAN 개발)
 *  2. 웹(Vercel): "/api" (서버리스 함수, CORS 불필요)
 *  3. 네이티브(iOS/Android): 프로덕션 https://ja-pyeong.vercel.app/api
 *     (개발 시는 EXPO_PUBLIC_API_BASE 로 LAN IP 지정)
 *
 * 인증:
 *  - secureStorage 의 "japyeong.auth.token" 키에 JWT 저장돼 있으면
 *    Authorization: Bearer <token> 자동 주입.
 *  - 토큰 갱신·로그아웃은 src/stores/authStore.ts 가 책임.
 *  - 401 발생 시 onUnauthorized 콜백 호출 (App 에서 store.clearAuth() 연결).
 */

import { Platform } from "react-native";

import { secureStorage } from "@/lib/secureStorage";

const PROD_API = "https://ja-pyeong.vercel.app/api";

export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE ??
  (Platform.OS === "web" ? "/api" : PROD_API);

export const TOKEN_KEY = "japyeong.auth.token";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public retryAfter?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** 레이트리밋(일일 한도) 도달 — paywall로 유도해야 함 */
  get isRateLimited(): boolean {
    return this.status === 429;
  }

  /** 회원 일일 한도 메시지에 "한도" 단어가 있으면 paywall 트리거 */
  get isPaywallTrigger(): boolean {
    return this.status === 429 && (
      this.message.includes("한도") || this.message.includes("구독")
    );
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }
}

// ── 401 글로벌 핸들러 (중복 트리거 차단) ────────────────────
let onUnauthorized: (() => void) | null = null;
let unauthorizedInFlight = false;
export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}
function triggerUnauthorized(): void {
  if (unauthorizedInFlight || !onUnauthorized) return;
  unauthorizedInFlight = true;
  try {
    onUnauthorized();
  } finally {
    // 다음 tick 에 풀어주기 — 동시 다발 401 묶음만 1회 처리
    setTimeout(() => {
      unauthorizedInFlight = false;
    }, 250);
  }
}

// ── 토큰 캐시 (메모리) — 빠른 접근 ──────────────────────
let cachedToken: string | null | undefined = undefined;  // undefined = 미초기화

export async function getAuthToken(): Promise<string | null> {
  if (cachedToken !== undefined) return cachedToken;
  cachedToken = await secureStorage.getItem(TOKEN_KEY);
  return cachedToken;
}

export async function setAuthToken(token: string | null): Promise<void> {
  cachedToken = token;
  if (token) {
    await secureStorage.setItem(TOKEN_KEY, token);
  } else {
    await secureStorage.removeItem(TOKEN_KEY);
  }
}

/** 외부 (멀티탭 storage 이벤트) 에서 토큰이 사라졌음을 알릴 때 호출.
 *  cachedToken 무효화 + 401 핸들러 트리거. */
export function invalidateCachedToken(): void {
  cachedToken = null;
  triggerUnauthorized();
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  const token = await getAuthToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });
  if (!res.ok) {
    let detail = friendlyStatus(res.status, res.statusText);
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string" && body.detail) {
        detail = body.detail;
      } else if (Array.isArray(body.detail)) {
        // FastAPI 422 validation — {detail: [{loc, msg, type}, ...]}
        const msgs = (body.detail as Array<{ msg?: string; loc?: string[] }>)
          .map((d) => d?.msg ?? "")
          .filter(Boolean);
        if (msgs.length) detail = msgs.join(" · ");
      }
    } catch {
      // ignore parse errors
    }
    const retryAfter = parseInt(res.headers.get("Retry-After") ?? "0", 10);
    if (res.status === 401) {
      triggerUnauthorized();
    }
    throw new ApiError(res.status, detail, retryAfter || undefined);
  }
  // 204 No Content
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}

export function patch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

// ── 상태 코드별 친화 메시지 ────────────────────────────
function friendlyStatus(status: number, fallback: string): string {
  if (status === 401) return "세션이 만료되었습니다. 다시 로그인해주세요.";
  if (status === 403) return "권한이 없습니다.";
  if (status === 404) return "요청한 리소스를 찾을 수 없습니다.";
  if (status === 429) return "요청이 많습니다. 잠시 후 다시 시도해주세요.";
  if (status === 503) return "일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.";
  if (status >= 500) return "서버 오류가 발생했습니다.";
  return fallback || "요청 처리 중 오류가 발생했습니다.";
}

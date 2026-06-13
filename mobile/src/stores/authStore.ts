/** 인증 상태 (Zustand) — JWT 보관 + 회원 정보 캐시.
 *
 * 흐름:
 *   1. App 부팅 → hydrate() 호출 → secureStorage 에서 token 로드
 *   2. token 있으면 fetchMe() 로 회원 정보 갱신 (만료/위변조 시 자동 로그아웃)
 *   3. login/signup 성공 → setAuth(token, user). fetchMe 실패 시 storage 롤백.
 *   4. logout → clearAuth() → storage 삭제 + API client cache 비움
 *
 * 401 핸들러: client.ts 의 setUnauthorizedHandler 에 연결되어
 * 백엔드가 401 응답할 때 자동으로 logout 실행 (중복 트리거는 client 가 차단).
 *
 * 동시성:
 *   - hydrate() 가 in-flight promise 를 모듈 스코프에 캐시 → StrictMode/Fast Refresh 시 중복 호출 차단.
 *   - login/signup/oauth catch 블록이 setAuthToken(null) 호출 → 상태 불일치 차단.
 *   - logout 후 도착한 fetchMe 응답이 user 를 부활시키지 않게 generation 카운터.
 */

import { create } from "zustand";

import {
  fetchMe,
  login as apiLogin,
  oauthLogin as apiOauth,
  signup as apiSignup,
  refreshToken as apiRefresh,
  type LoginBody,
  type MeResponse,
  type OAuthBody,
  type SignupBody,
} from "@/api/auth";
import {
  invalidateCachedToken,
  setAuthToken,
  setUnauthorizedHandler,
  TOKEN_KEY,
} from "@/api/client";
import { attachWebStorageListener, secureStorage } from "@/lib/secureStorage";

interface AuthState {
  // 상태
  ready: boolean;        // hydrate 완료 여부 (스플래시 게이팅용)
  token: string | null;
  user: MeResponse | null;
  loading: boolean;
  error: string | null;
  // 신규 OAuth/회원가입 사용자 — onboarding 라우팅 신호
  isNewlyRegistered: boolean;

  // 액션
  hydrate: () => Promise<void>;
  signup: (body: SignupBody) => Promise<void>;
  login: (body: LoginBody) => Promise<void>;
  oauthLogin: (body: OAuthBody) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
  // 구독 결제·해지 직후 JWT 재발급 → tier 클레임 즉시 갱신(한도·모델 반영)
  refreshSession: () => Promise<void>;
  clearError: () => void;
  consumeIsNewly: () => boolean;
}

// 모듈 스코프 — hydrate 중복 호출 방지
let hydratePromise: Promise<void> | null = null;
// 모듈 스코프 — logout 시 generation 증가 → 진행 중이던 fetchMe 가 무시
let generation = 0;
let storageDetach: (() => void) | null = null;

export const useAuthStore = create<AuthState>((set, get) => ({
  ready: false,
  token: null,
  user: null,
  loading: false,
  error: null,
  isNewlyRegistered: false,

  async hydrate() {
    if (hydratePromise) return hydratePromise;
    if (get().ready) return;
    hydratePromise = (async () => {
      // 401 → 자동 로그아웃 (모든 await 이전에 등록 — 자체 fetchMe 401 도 잡힘)
      setUnauthorizedHandler(() => {
        void get().logout();
      });
      // 웹 멀티탭: 다른 탭 로그아웃 → 현재 탭 캐시 무효화 + logout
      if (!storageDetach) {
        storageDetach = attachWebStorageListener(TOKEN_KEY, () => {
          invalidateCachedToken();
          void get().logout();
        });
      }

      try {
        const stored = await secureStorage.getItem(TOKEN_KEY);
        if (!stored) {
          set({ ready: true });
          return;
        }
        await setAuthToken(stored);
        set({ token: stored });
        try {
          const me = await fetchMe();
          set({ user: me, ready: true });
        } catch {
          // 만료/위조 토큰 — 조용히 로그아웃
          await setAuthToken(null);
          set({ token: null, user: null, ready: true });
        }
      } catch {
        set({ ready: true });
      }
    })();
    try {
      await hydratePromise;
    } finally {
      // hydrate 끝나면 promise 해제 — 다음 호출은 ready 가드로 빠짐
      hydratePromise = null;
    }
  },

  async signup(body) {
    set({ loading: true, error: null });
    const myGen = ++generation;
    try {
      const res = await apiSignup(body);
      await setAuthToken(res.token);
      const me = await fetchMe();
      if (myGen !== generation) return;  // logout 이 그 사이 발생 — 무시
      set({
        token: res.token,
        user: me,
        loading: false,
        isNewlyRegistered: true,
      });
    } catch (e) {
      // 상태 불일치 차단: storage·cache 롤백
      if (myGen === generation) {
        await setAuthToken(null);
        set({ token: null, user: null, loading: false, error: _msg(e) });
      }
      throw e;
    }
  },

  async login(body) {
    set({ loading: true, error: null });
    const myGen = ++generation;
    try {
      const res = await apiLogin(body);
      await setAuthToken(res.token);
      const me = await fetchMe();
      if (myGen !== generation) return;
      set({ token: res.token, user: me, loading: false });
    } catch (e) {
      if (myGen === generation) {
        await setAuthToken(null);
        set({ token: null, user: null, loading: false, error: _msg(e) });
      }
      throw e;
    }
  },

  async oauthLogin(body) {
    set({ loading: true, error: null });
    const myGen = ++generation;
    try {
      const res = await apiOauth(body);
      await setAuthToken(res.token);
      const me = await fetchMe();
      if (myGen !== generation) return;
      set({
        token: res.token,
        user: me,
        loading: false,
        isNewlyRegistered: !!res.is_new,
      });
    } catch (e) {
      if (myGen === generation) {
        await setAuthToken(null);
        set({ token: null, user: null, loading: false, error: _msg(e) });
      }
      throw e;
    }
  },

  async logout() {
    // generation 증가 → 진행 중이던 in-flight 가 무시됨
    generation++;
    await setAuthToken(null);
    set({
      token: null,
      user: null,
      error: null,
      isNewlyRegistered: false,
    });
  },

  async refreshMe() {
    if (!get().token) return;
    const myGen = generation;
    try {
      const me = await fetchMe();
      if (myGen !== generation) return;
      set({ user: me });
    } catch {
      // 토큰 만료 → 401 핸들러가 처리
    }
  },

  async refreshSession() {
    if (!get().token) return;
    const myGen = generation;
    try {
      const res = await apiRefresh(); // 서버가 현재 활성 구독 tier 로 JWT 재발급
      if (myGen !== generation) return; // 그 사이 logout → 무시
      await setAuthToken(res.token);
      const cur = get().user;
      set({
        token: res.token,
        user: cur ? { ...cur, tier: res.tier } : cur,
      });
    } catch {
      // refresh 실패 — 기존 토큰 유지 (다음 기회에 재시도)
    }
  },

  clearError() {
    set({ error: null });
  },

  consumeIsNewly() {
    const flag = get().isNewlyRegistered;
    if (flag) set({ isNewlyRegistered: false });
    return flag;
  },
}));

function _msg(e: unknown): string {
  if (e instanceof Error) return e.message;
  return "알 수 없는 오류가 발생했습니다.";
}

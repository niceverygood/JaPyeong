/** 토큰 저장 — 네이티브는 SecureStore(키체인), 웹은 localStorage.
 *
 * SecureStore:
 *   - iOS Keychain (디바이스 잠금 시 보호)
 *   - Android Keystore (encrypted at rest)
 *   - 웹 미지원 → 폴백
 *
 * 웹 폴백:
 *   - localStorage. XSS 노출 가능성 있으니 백엔드에서 JWT TTL 짧게 유지 + refresh.
 *   - Vercel 같은 SaaS 환경에서 secure cookie 가 더 좋지만 RN-web 호환성 위해 storage.
 */

import { Platform } from "react-native";

interface SecureStorage {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

function makeWebStorage(): SecureStorage {
  return {
    async getItem(key) {
      try {
        if (typeof globalThis.localStorage === "undefined") return null;
        return globalThis.localStorage.getItem(key);
      } catch {
        return null;
      }
    },
    async setItem(key, value) {
      try {
        if (typeof globalThis.localStorage === "undefined") return;
        globalThis.localStorage.setItem(key, value);
      } catch {
        // 일부 환경 (privacy mode) 거부 — silent ignore
      }
    },
    async removeItem(key) {
      try {
        if (typeof globalThis.localStorage === "undefined") return;
        globalThis.localStorage.removeItem(key);
      } catch {
        /* ignore */
      }
    },
  };
}

/** 웹: 다른 탭에서 토큰이 변경/삭제되면 현재 탭의 캐시 무효화 + 로그아웃 트리거.
 *  네이티브에는 의미 없음 (다른 프로세스가 SecureStore 건드릴 일 없음). */
export function attachWebStorageListener(
  tokenKey: string,
  onInvalidate: () => void,
): () => void {
  if (Platform.OS !== "web" || typeof globalThis.addEventListener !== "function") {
    return () => {};
  }
  const handler = (event: Event) => {
    const e = event as { key?: string | null; newValue?: string | null };
    if (e.key === tokenKey || e.key === null) {
      if (!e.newValue) onInvalidate();
    }
  };
  globalThis.addEventListener("storage", handler);
  return () => {
    globalThis.removeEventListener("storage", handler);
  };
}

function makeNativeStorage(): SecureStorage {
  // 동적 import — 웹 번들에서 expo-secure-store 가 import 되지 않게.
  // require 가 RN-web 에서 throw 하지 않게 try.
  let store: typeof import("expo-secure-store") | null = null;
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    store = require("expo-secure-store");
  } catch {
    store = null;
  }
  if (!store) {
    return makeWebStorage();  // 안전한 폴백
  }
  return {
    async getItem(key) {
      return await store!.getItemAsync(key);
    },
    async setItem(key, value) {
      await store!.setItemAsync(key, value, {
        // iOS: 디바이스 잠금 풀린 상태에서만 접근. 다른 디바이스 백업 X.
        keychainAccessible: store!.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
      });
    },
    async removeItem(key) {
      await store!.deleteItemAsync(key);
    },
  };
}

export const secureStorage: SecureStorage =
  Platform.OS === "web" ? makeWebStorage() : makeNativeStorage();

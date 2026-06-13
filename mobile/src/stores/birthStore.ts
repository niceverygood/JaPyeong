/** 사용자 출생정보 상태 (Zustand) — 영속화.
 *
 * secureStorage(iOS Keychain / Android Keystore, 웹 localStorage 폴백)에 저장한다.
 * 콜드 스타트에도 명식이 유지된다(재방문 시 0탭으로 가치 도달). 생년월일·이름은
 * 개인정보(PIPA/GDPR)라 평문 AsyncStorage 가 아닌 암호화 저장소를 쓴다.
 * 이전에는 in-memory 라 앱 재실행마다 birth=null → 매번 재입력해야 했음(리텐션 킬러).
 */

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { BirthInput } from "@/api/types";
import { secureStorage } from "@/lib/secureStorage";

interface BirthState {
  birth: BirthInput | null;
  hydrated: boolean; // persist 복원 완료 여부
  setBirth: (birth: BirthInput) => void;
  clear: () => void;
}

export const useBirthStore = create<BirthState>()(
  persist(
    (set) => ({
      birth: null,
      hydrated: false,
      setBirth: (birth) => set({ birth }),
      clear: () => set({ birth: null }),
    }),
    {
      name: "japyeong-birth",
      storage: createJSONStorage(() => secureStorage),
      partialize: (s) => ({ birth: s.birth }),
      onRehydrateStorage: () => (state) => {
        // 복원 완료(저장된 값 없음 포함) → hydrated=true 로 게이팅 해제
        useBirthStore.setState({ hydrated: true });
        void state;
      },
    },
  ),
);

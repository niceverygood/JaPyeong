/** 사용자 출생정보 상태 (Zustand) — 영속화.
 *
 * AsyncStorage 에 저장해 콜드 스타트에도 명식이 유지된다(재방문 시 0탭으로 가치 도달).
 * 이전에는 in-memory 라 앱 재실행마다 birth=null → 매번 생년월일 재입력해야 했음(리텐션 킬러).
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { BirthInput } from "@/api/types";

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
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (s) => ({ birth: s.birth }),
      onRehydrateStorage: () => (state) => {
        if (state) state.hydrated = true;
      },
    },
  ),
);

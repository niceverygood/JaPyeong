/** 사용자 출생정보 상태 (Zustand). */

import { create } from "zustand";

import type { BirthInput } from "@/api/types";

interface BirthState {
  birth: BirthInput | null;
  setBirth: (birth: BirthInput) => void;
  clear: () => void;
}

export const useBirthStore = create<BirthState>((set) => ({
  birth: null,
  setBirth: (birth) => set({ birth }),
  clear: () => set({ birth: null }),
}));

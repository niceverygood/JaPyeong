/** 전역 네비게이션 ref — NavigationContainer 바깥(Paywall 등)에서 라우팅할 때 사용. */

import { createNavigationContainerRef } from "@react-navigation/native";

import type { RootStackParamList } from "./types";

export const navigationRef = createNavigationContainerRef<RootStackParamList>();

export function navigate<T extends keyof RootStackParamList>(
  name: T,
  params?: RootStackParamList[T],
): void {
  if (navigationRef.isReady()) {
    // @ts-expect-error — params 가 undefined 인 라우트 호환
    navigationRef.navigate(name, params);
  }
}

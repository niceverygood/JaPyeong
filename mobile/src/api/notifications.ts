/** /v1/notifications API — 푸시 토큰 등록 + 수신 설정. */

import { useMutation } from "@tanstack/react-query";

import { post } from "./client";

export type Platform = "ios" | "android" | "web";

export interface RegisterTokenRequest {
  expo_push_token: string;
  platform: Platform;
  // Sprint 1-2 회원 도입 후 jwt 헤더에서 user_id 추출
}

export interface RegisterTokenResponse {
  ok: boolean;
  token_id?: number;
}

export interface NotificationPrefRequest {
  daily_fortune_enabled: boolean;       // 일진 daily push on/off
  daily_fortune_time_hhmm?: string;     // "07:30" 형식 (기본 08:00)
  negative_fortune_muted?: boolean;     // 부정 통변 알림만 끄기 (자평 가드 #9)
}

export function sendRegisterToken(
  req: RegisterTokenRequest,
): Promise<RegisterTokenResponse> {
  return post<RegisterTokenResponse>("/v1/notifications/register-token", req);
}

export function sendUpdatePrefs(
  req: NotificationPrefRequest,
): Promise<{ ok: boolean }> {
  return post<{ ok: boolean }>("/v1/notifications/preferences", req);
}

export function useRegisterToken() {
  return useMutation({ mutationFn: sendRegisterToken });
}

export function useUpdatePrefs() {
  return useMutation({ mutationFn: sendUpdatePrefs });
}

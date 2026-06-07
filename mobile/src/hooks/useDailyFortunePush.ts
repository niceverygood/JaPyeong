/**
 * useDailyFortunePush — 일진 daily push 권한 요청 + 토큰 등록.
 *
 * 자평 가드레일 (BM v2 정체성):
 *   - 권한 요청은 사용자가 명시적으로 "켜기" 누를 때만 (다크 패턴 X)
 *   - 끄기는 마이페이지 1depth (다크 패턴 차단)
 *   - 부정 통변 알림만 끄기 토글 별도 제공
 *
 * Expo Push Notification 사용 (네이티브 빌드 필수, 웹은 미지원).
 */

import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { useCallback, useState } from "react";
import { Platform } from "react-native";

import { sendRegisterToken } from "@/api/notifications";

export interface PushRegistrationState {
  loading: boolean;
  granted: boolean;
  error: string | null;
  expoPushToken: string | null;
}

export interface UseDailyFortunePushResult extends PushRegistrationState {
  /** 권한 요청 + 토큰 등록 (사용자가 "알림 받기" 누를 때 호출). */
  requestAndRegister: () => Promise<void>;
}

export function useDailyFortunePush(): UseDailyFortunePushResult {
  const [state, setState] = useState<PushRegistrationState>({
    loading: false,
    granted: false,
    error: null,
    expoPushToken: null,
  });

  const requestAndRegister = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));

    try {
      // 1. 웹은 push 미지원 (앱 전용)
      if (Platform.OS === "web") {
        setState({
          loading: false,
          granted: false,
          error: "푸시 알림은 모바일 앱에서만 가능합니다.",
          expoPushToken: null,
        });
        return;
      }

      // 2. 실기기 여부 (시뮬레이터는 push 토큰 못 받음)
      if (!Device.isDevice) {
        setState({
          loading: false,
          granted: false,
          error: "시뮬레이터에서는 푸시를 받을 수 없습니다 (실기기 필요).",
          expoPushToken: null,
        });
        return;
      }

      // 3. 권한 요청 (사용자 명시적 허용 필요)
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      if (existingStatus !== "granted") {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }
      if (finalStatus !== "granted") {
        setState({
          loading: false,
          granted: false,
          error: "푸시 권한이 거부되었습니다. 설정에서 허용해 주세요.",
          expoPushToken: null,
        });
        return;
      }

      // 4. Expo 푸시 토큰 발급 — projectId 는 EAS Build 시 자동
      const tokenData = await Notifications.getExpoPushTokenAsync();
      const expoPushToken = tokenData.data;

      // 5. 백엔드에 토큰 등록 (실패해도 권한은 살아있으니 best-effort)
      try {
        await sendRegisterToken({
          expo_push_token: expoPushToken,
          platform: Platform.OS as "ios" | "android" | "web",
        });
      } catch (e) {
        // 백엔드 등록 실패는 silent — 다음 앱 시작 때 재시도 가능
        console.warn("[push] 토큰 등록 실패 (백엔드):", e);
      }

      // 6. 안드로이드 채널 (Android 8.0+ 필수)
      if (Platform.OS === "android") {
        await Notifications.setNotificationChannelAsync("daily-fortune", {
          name: "일진 알림",
          importance: Notifications.AndroidImportance.DEFAULT,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: "#C9A961",
        });
      }

      setState({
        loading: false,
        granted: true,
        error: null,
        expoPushToken,
      });
    } catch (e) {
      setState({
        loading: false,
        granted: false,
        error: e instanceof Error ? e.message : String(e),
        expoPushToken: null,
      });
    }
  }, []);

  return { ...state, requestAndRegister };
}

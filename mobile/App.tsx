import "./global.css";

import { DarkTheme, NavigationContainer } from "@react-navigation/native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import * as SplashScreen from "expo-splash-screen";
import { StatusBar } from "expo-status-bar";
import { useEffect, useMemo } from "react";
import { Platform, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { ApiError } from "@/api/client";
import { PaywallProvider, usePaywall } from "@/components/primitives/Paywall";
import { navigationRef } from "@/navigation/navRef";
import { RootNavigator } from "@/navigation/RootNavigator";
import { useAuthStore } from "@/stores/authStore";
import { useBirthStore } from "@/stores/birthStore";
import { colors } from "@/theme";

// 폰트 로드 동안 스플래시 유지
SplashScreen.preventAutoHideAsync().catch(() => {});

// QueryClient는 PaywallProvider 안에서 생성해 onError에서 paywall 접근 가능하게 함

const navTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: colors.bg.base,
    card: colors.bg.base,
    text: colors.text.primary,
    primary: colors.gold.primary,
    border: colors.line,
  },
};

export default function App() {
  // 네이티브에서만 Pretendard 번들 로드 — 웹은 global.css 의 CDN
  const [fontsLoaded, fontError] = useFonts(
    Platform.OS === "web"
      ? {}
      : {
          "Pretendard Variable": require("./assets/fonts/PretendardVariable.ttf"),
        },
  );

  const hydrate = useAuthStore((s) => s.hydrate);
  const authReady = useAuthStore((s) => s.ready);
  // 명식(secureStorage) 복원 완료 여부 — 복원 전 렌더 시 '명식 없음' 깜빡임 방지
  const birthHydrated = useBirthStore((s) => s.hydrated);

  // 부팅 시 1회만 JWT hydrate (secureStorage → 메모리 캐시)
  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  useEffect(() => {
    if ((fontsLoaded || fontError) && authReady && birthHydrated) {
      SplashScreen.hideAsync().catch(() => {});
    }
  }, [fontsLoaded, fontError, authReady, birthHydrated]);

  if ((!fontsLoaded && !fontError) || !authReady || !birthHydrated) {
    return <View style={{ flex: 1, backgroundColor: colors.bg.base }} />;
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <PaywallProvider>
        <QueryWithPaywall>
          <NavigationContainer theme={navTheme} ref={navigationRef}>
            <RootNavigator />
          </NavigationContainer>
        </QueryWithPaywall>
      </PaywallProvider>
    </SafeAreaProvider>
  );
}

/** TanStack Query 전역 에러 핸들러 — 429 paywall 트리거 응답을 자동으로 모달로 변환. */
function QueryWithPaywall({ children }: { children: React.ReactNode }) {
  const { showPaywall } = usePaywall();
  const queryClient = useMemo(
    () =>
      new QueryClient({
        defaultOptions: {
          mutations: {
            onError: (err) => {
              if (err instanceof ApiError && err.isPaywallTrigger) {
                showPaywall(err.retryAfter);
              }
            },
          },
        },
      }),
    [showPaywall],
  );
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

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
import { RootNavigator } from "@/navigation/RootNavigator";
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

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync().catch(() => {});
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) {
    return <View style={{ flex: 1, backgroundColor: colors.bg.base }} />;
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <PaywallProvider>
        <QueryWithPaywall>
          <NavigationContainer theme={navTheme}>
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

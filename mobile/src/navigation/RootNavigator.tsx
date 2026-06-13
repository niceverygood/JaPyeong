import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { AuthLandingScreen } from "@/screens/Auth/AuthLandingScreen";
import { LoginScreen } from "@/screens/Auth/LoginScreen";
import { ProfileScreen } from "@/screens/Auth/ProfileScreen";
import { SignupScreen } from "@/screens/Auth/SignupScreen";
import { ChatScreen } from "@/screens/Chat/ChatScreen";
import { CompatibilityScreen } from "@/screens/Compatibility/CompatibilityScreen";
import { DateSelectionScreen } from "@/screens/DateSelection/DateSelectionScreen";
import { DecisionScreen } from "@/screens/Decision/DecisionScreen";
import { LandingScreen } from "@/screens/Landing/LandingScreen";
import { NotificationsScreen } from "@/screens/Notifications/NotificationsScreen";
import { OnboardingScreen } from "@/screens/Onboarding/OnboardingScreen";
import { CheckoutScreen } from "@/screens/Payment/CheckoutScreen";
import { PaymentResultScreen } from "@/screens/Payment/PaymentResultScreen";
import { PlansScreen } from "@/screens/Payment/PlansScreen";
import { SajuScreen } from "@/screens/Saju/SajuScreen";
import { useAuthStore } from "@/stores/authStore";
import { colors } from "@/theme";

import type { RootStackParamList } from "./types";

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  // 토큰이 있으면 Landing 먼저, 없으면 AuthLanding 먼저.
  // 명식 입력 등은 비로그인도 가능하게 유지 — Landing 자체는 게이트하지 않음.
  // 결제·자문위원·일진 알림 등은 화면 진입 시 token 체크.
  const token = useAuthStore((s) => s.token);
  const initial: keyof RootStackParamList = token ? "Landing" : "AuthLanding";

  return (
    <Stack.Navigator
      initialRouteName={initial}
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg.base },
        headerTintColor: colors.gold.primary,
        headerTitleStyle: { color: colors.text.primary },
        contentStyle: { backgroundColor: colors.bg.base },
      }}
    >
      {/* 인증 그룹 */}
      <Stack.Screen
        name="AuthLanding"
        component={AuthLandingScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Login"
        component={LoginScreen}
        options={{ title: "로그인", headerBackTitle: "" }}
      />
      <Stack.Screen
        name="Signup"
        component={SignupScreen}
        options={{ title: "회원가입", headerBackTitle: "" }}
      />
      <Stack.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ title: "내 정보" }}
      />

      {/* 메인 그룹 */}
      <Stack.Screen
        name="Landing"
        component={LandingScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Onboarding"
        component={OnboardingScreen}
        options={{ title: "명식 입력", headerBackTitle: "처음" }}
      />
      <Stack.Screen name="Saju" component={SajuScreen} options={{ title: "명식 분석" }} />
      <Stack.Screen name="Chat" component={ChatScreen} options={{ title: "자평 자문" }} />
      <Stack.Screen
        name="Compatibility"
        component={CompatibilityScreen}
        options={{ title: "궁합" }}
      />
      <Stack.Screen
        name="DateSelection"
        component={DateSelectionScreen}
        options={{ title: "택일" }}
      />
      <Stack.Screen
        name="Decision"
        component={DecisionScreen}
        options={{ title: "결정 도우미" }}
      />
      <Stack.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{ title: "알림 설정" }}
      />

      {/* 결제 그룹 */}
      <Stack.Screen
        name="Plans"
        component={PlansScreen}
        options={{ title: "구독 플랜" }}
      />
      <Stack.Screen
        name="Checkout"
        component={CheckoutScreen}
        options={{ title: "결제" }}
      />
      <Stack.Screen
        name="PaymentResult"
        component={PaymentResultScreen}
        options={{ title: "결제 결과", headerBackTitle: "" }}
      />
    </Stack.Navigator>
  );
}

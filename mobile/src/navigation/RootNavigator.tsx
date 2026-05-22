import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { LandingScreen } from "@/screens/Landing/LandingScreen";
import { OnboardingScreen } from "@/screens/Onboarding/OnboardingScreen";
import { SajuScreen } from "@/screens/Saju/SajuScreen";
import { colors } from "@/theme";

import type { RootStackParamList } from "./types";

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Landing"
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg.base },
        headerTintColor: colors.gold.primary,
        headerTitleStyle: { color: colors.text.primary },
        contentStyle: { backgroundColor: colors.bg.base },
      }}
    >
      <Stack.Screen
        name="Landing"
        component={LandingScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Onboarding"
        component={OnboardingScreen}
        options={{ title: "출생 정보", headerBackTitle: "처음" }}
      />
      <Stack.Screen name="Saju" component={SajuScreen} options={{ title: "원국 분석" }} />
    </Stack.Navigator>
  );
}

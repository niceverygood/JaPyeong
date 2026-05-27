import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { ChatScreen } from "@/screens/Chat/ChatScreen";
import { CompatibilityScreen } from "@/screens/Compatibility/CompatibilityScreen";
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
        options={{ title: "명식 입력", headerBackTitle: "처음" }}
      />
      <Stack.Screen name="Saju" component={SajuScreen} options={{ title: "명식 분석" }} />
      <Stack.Screen name="Chat" component={ChatScreen} options={{ title: "자평 자문" }} />
      <Stack.Screen
        name="Compatibility"
        component={CompatibilityScreen}
        options={{ title: "궁합" }}
      />
    </Stack.Navigator>
  );
}

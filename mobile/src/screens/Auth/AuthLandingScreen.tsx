/** 인증 진입 화면 — 로그인/회원가입 선택 + OAuth 버튼.
 *
 * 디자인:
 *   - 자평 정체성 유지 (자, 평 호환 표기)
 *   - 카카오/애플 우선 (한국 사용자 기준)
 *   - 이메일/비밀번호는 보조
 *   - 워드마크에 accessibilityLabel="자평" 명시 (VoiceOver 한국어 발음)
 *   - Apple 버튼 라벨 명시 (시각·시각장애 사용자 모두 인지)
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button } from "@/components/primitives/Button";
import type { RootStackParamList } from "@/navigation/types";

type Nav = NativeStackNavigationProp<RootStackParamList, "AuthLanding">;

export function AuthLandingScreen() {
  const navigation = useNavigation<Nav>();

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <View className="flex-1 px-6 pt-16">
        {/* 워드마크 — 스크린리더 한자 음독 회피 */}
        <View
          accessible
          accessibilityRole="header"
          accessibilityLabel="자평. 명리 AI 자문"
          className="items-center"
        >
          <Text className="font-serif text-[44px] leading-[50px] text-ink">
            子<Text className="text-gold">平</Text>
          </Text>
          <Text className="mt-2 font-sans text-xs tracking-[0.3em] text-ink-muted">
            JAPYEONG
          </Text>
        </View>

        <View className="mt-12">
          <Text className="text-center font-serif text-2xl text-ink">
            결정 앞에, 자평
          </Text>
          <Text className="mt-3 text-center font-sans text-sm text-ink-secondary">
            지금 흐름을 보고{"\n"}큰 결정을 더 분명하게.
          </Text>
        </View>

        <View className="mt-auto pb-10">
          {/* OAuth (실 SDK 통합 전 placeholder — production 빌드에선 백엔드가 503 반환) */}
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="카카오로 시작하기"
            onPress={() => navigation.navigate("Login", { provider: "kakao" })}
            className="mb-3 h-14 items-center justify-center rounded-lg active:opacity-80"
            style={{ backgroundColor: "#FEE500" }}
            testID="oauth-kakao"
          >
            <Text className="font-sans text-base font-semibold text-black">
              카카오로 시작
            </Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Apple로 시작하기"
            onPress={() => navigation.navigate("Login", { provider: "apple" })}
            className="mb-3 h-14 items-center justify-center rounded-lg active:opacity-80"
            style={{ backgroundColor: "#000000", borderWidth: 1, borderColor: "#222" }}
            testID="oauth-apple"
          >
            <Text className="font-sans text-base font-semibold text-white">
              Apple로 시작
            </Text>
          </Pressable>

          {/* 구분선 */}
          <View className="my-4 flex-row items-center">
            <View className="h-px flex-1 bg-line" />
            <Text className="mx-3 font-sans text-xs text-ink-muted">또는</Text>
            <View className="h-px flex-1 bg-line" />
          </View>

          {/* 이메일 */}
          <Button
            label="이메일로 로그인"
            variant="ghost"
            onPress={() => navigation.navigate("Login", {})}
            testID="cta-email-login"
          />

          <Pressable
            accessibilityRole="link"
            accessibilityLabel="회원가입 화면으로 이동"
            onPress={() => navigation.navigate("Signup")}
            className="mt-3 items-center py-3"
          >
            <Text className="font-sans text-sm text-ink-secondary">
              아직 회원이 아니신가요? <Text className="text-gold">회원가입</Text>
            </Text>
          </Pressable>

          <Text className="mt-6 text-center font-sans text-[11px] leading-[16px] text-ink-faint">
            계속 진행하면 <Text className="text-ink-muted">서비스 이용약관</Text>과{"\n"}
            <Text className="text-ink-muted">개인정보 처리방침</Text>에 동의한 것으로 봅니다.
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

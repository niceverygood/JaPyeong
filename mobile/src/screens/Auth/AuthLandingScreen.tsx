/** 인증 진입 화면 — 로그인/회원가입 선택 + OAuth 버튼.
 *
 * 디자인:
 *   - 자평 정체성 유지 (자, 평 호환 표기)
 *   - 이메일 가입/로그인 + 비로그인 둘러보기 (OAuth 는 실 SDK 구현 후 복원)
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
          {/* 카카오/Apple OAuth 는 실 SDK·서버 검증 구현 후 복원
              (placeholder 상태로 노출하면 영구 503 — App Review 2.1 재거절 사유) */}
          <Button
            label="이메일로 시작"
            onPress={() => navigation.navigate("Signup")}
            testID="cta-email-signup"
          />

          <View className="mt-3">
            <Button
              label="로그인"
              variant="ghost"
              onPress={() => navigation.navigate("Login", {})}
              testID="cta-email-login"
            />
          </View>

          <Pressable
            accessibilityRole="link"
            accessibilityLabel="로그인 없이 둘러보기"
            onPress={() => navigation.navigate("Landing")}
            className="mt-3 items-center py-3"
            testID="cta-guest-browse"
          >
            <Text className="font-sans text-sm text-ink-secondary">
              로그인 없이 <Text className="text-gold">둘러보기</Text>
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

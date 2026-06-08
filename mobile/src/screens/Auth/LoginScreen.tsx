/** 이메일+비밀번호 로그인 화면.
 *
 * 추가:
 *   - route.params.provider: "kakao" | "apple" 인 경우 향후 native OAuth 띄움.
 *     현재는 백엔드 placeholder OAuth 엔드포인트로 폴백 (dev/staging 만 활성).
 *     production 빌드에서는 OAuth 버튼이 비활성화돼야 함 (실 SDK 도입 후 활성).
 *   - 에러 메시지는 친화적 한국어로 매핑 (client.ts friendlyStatus + 백엔드 detail).
 */

import { useNavigation, useRoute, type RouteProp } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useCallback, useRef, useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button } from "@/components/primitives/Button";
import { Field } from "@/components/primitives/Field";
import type { RootStackParamList } from "@/navigation/types";
import { useAuthStore } from "@/stores/authStore";

type Nav = NativeStackNavigationProp<RootStackParamList, "Login">;
type Route = RouteProp<RootStackParamList, "Login">;

export function LoginScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<Route>();
  const provider = route.params?.provider;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const passwordRef = useRef<TextInput>(null);
  const loading = useAuthStore((s) => s.loading);
  const error = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const loginAction = useAuthStore((s) => s.login);
  const oauthAction = useAuthStore((s) => s.oauthLogin);
  const consumeIsNewly = useAuthStore((s) => s.consumeIsNewly);

  const isOauthFlow = provider === "kakao" || provider === "apple";
  const isEmailValid = /\S+@\S+\.\S+/.test(email);
  // 백엔드 LoginRequest 는 min_length=1 — legacy 계정 호환
  const isFormValid = isOauthFlow || (isEmailValid && password.length >= 1);

  const handleSubmit = useCallback(async () => {
    clearError();
    try {
      if (isOauthFlow && provider) {
        // TODO: 실 SDK (kakao-rn / expo-apple-authentication) 통합 시 교체.
        // 현재는 백엔드 OAUTH_PLACEHOLDER_ENABLED 인 dev/staging 환경에서만 동작.
        await oauthAction({
          provider,
          subject: `dev_${provider}_subject_${Date.now()}`,
          email: email || `${provider}_user_${Date.now()}@example.com`,
        });
      } else {
        await loginAction({ email, password });
      }
      // 신규 OAuth 가입자는 명식 입력 (Onboarding) 으로
      const isNew = consumeIsNewly();
      navigation.reset({
        index: 0,
        routes: isNew ? [{ name: "Landing" }, { name: "Onboarding" }] : [{ name: "Landing" }],
      });
    } catch {
      // store 가 친화적 error 메시지 셋팅 — 화면에서 노출
    }
  }, [clearError, consumeIsNewly, email, isOauthFlow, loginAction, navigation, oauthAction, password, provider]);

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <KeyboardAvoidingView
        className="flex-1"
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView
          contentContainerStyle={{ flexGrow: 1, paddingHorizontal: 24, paddingTop: 24 }}
          keyboardShouldPersistTaps="handled"
        >
          <Text className="mb-2 font-serif text-2xl text-ink">
            {isOauthFlow
              ? `${provider === "kakao" ? "카카오" : "Apple"} 로그인`
              : "로그인"}
          </Text>
          <Text className="mb-8 font-sans text-sm text-ink-secondary">
            {isOauthFlow
              ? "외부 인증으로 계속합니다."
              : "이메일과 비밀번호를 입력해주세요."}
          </Text>

          <Field
            label="이메일"
            value={email}
            onChangeText={(v) => {
              setEmail(v);
              if (error) clearError();
            }}
            placeholder="you@example.com"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="email"
            textContentType="emailAddress"
            returnKeyType="next"
            onSubmitEditing={() => passwordRef.current?.focus()}
            blurOnSubmit={false}
            testID="login-email"
          />
          {!isOauthFlow && (
            <Field
              ref={passwordRef}
              label="비밀번호"
              value={password}
              onChangeText={(v) => {
                setPassword(v);
                if (error) clearError();
              }}
              placeholder="••••••••"
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
              autoComplete="password"
              textContentType="password"
              returnKeyType="go"
              onSubmitEditing={() => isFormValid && handleSubmit()}
              testID="login-password"
            />
          )}

          {error && (
            <View
              accessibilityLiveRegion="polite"
              className="mb-4 rounded-md border border-state-warning/40 bg-state-warning/10 px-3 py-2"
            >
              <Text className="font-sans text-sm text-state-warning">
                {error}
              </Text>
            </View>
          )}

          <View className="mt-2">
            <Button
              label={loading ? "처리 중…" : (isOauthFlow ? "계속" : "로그인")}
              onPress={handleSubmit}
              loading={loading}
              disabled={!isFormValid}
              accessibilityLabel={loading ? "로그인 처리 중" : (isOauthFlow ? "OAuth 로그인 계속하기" : "로그인하기")}
              testID="login-submit"
            />
          </View>

          {!isOauthFlow && (
            <View className="mt-6 flex-row justify-center">
              <Text className="font-sans text-sm text-ink-secondary">
                계정이 없으신가요?{" "}
              </Text>
              <Text
                accessibilityRole="link"
                className="font-sans text-sm text-gold"
                onPress={() => navigation.navigate("Signup")}
              >
                회원가입
              </Text>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

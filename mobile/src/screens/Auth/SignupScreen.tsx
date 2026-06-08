/** 이메일·비밀번호 회원가입 + 마케팅 동의 옵션.
 *
 * 가드:
 *   - 비밀번호 8자 이상, 72자 이하 (bcrypt 제한)
 *   - 이메일 정규식: 더블닷·짧은 TLD 차단 (백엔드 Pydantic EmailStr 와 align)
 *   - 마케팅 동의는 default OFF (옵션) — 개인정보보호법 + BM v2 다크패턴 차단
 *
 * UX:
 *   - touched 상태로 첫 blur 이후에만 인라인 에러 노출 (타이핑 중 좌절 차단)
 *   - 비밀번호는 secureTextEntry + textContentType="newPassword" → iOS Keychain 자동제안
 *   - returnKeyType / onSubmitEditing 으로 폼 이동 자연스럽게
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useRef, useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button } from "@/components/primitives/Button";
import { Field } from "@/components/primitives/Field";
import type { RootStackParamList } from "@/navigation/types";
import { useAuthStore } from "@/stores/authStore";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "Signup">;

// 백엔드 Pydantic EmailStr 와 align — 짧은 TLD/더블닷 차단
const EMAIL_RE = /^[^\s@]+@[^\s@.]+(\.[^\s@.]+)+$/;

export function SignupScreen() {
  const navigation = useNavigation<Nav>();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [marketingConsent, setMarketingConsent] = useState(false);

  // touched: 첫 blur 후에만 인라인 에러 표시
  const [touched, setTouched] = useState<{ [k: string]: boolean }>({});

  const passwordRef = useRef<TextInput>(null);
  const passwordConfirmRef = useRef<TextInput>(null);

  const loading = useAuthStore((s) => s.loading);
  const error = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const signupAction = useAuthStore((s) => s.signup);
  const consumeIsNewly = useAuthStore((s) => s.consumeIsNewly);

  const emailValid = EMAIL_RE.test(email);
  const passwordValid = password.length >= 8 && password.length <= 72;
  const passwordMatches = password === passwordConfirm;
  const isFormValid = emailValid && passwordValid && passwordMatches;

  const handleSubmit = async () => {
    clearError();
    // submit 시도 → 모든 필드 touched
    setTouched({ email: true, password: true, passwordConfirm: true });
    if (!isFormValid) return;
    try {
      await signupAction({
        email,
        password,
        name: name || undefined,
        phone: phone || undefined,
        marketing_consent: marketingConsent,
      });
      // 신규 가입 → 명식 입력 (Onboarding) 으로
      const isNew = consumeIsNewly();
      navigation.reset({
        index: 0,
        routes: isNew ? [{ name: "Landing" }, { name: "Onboarding" }] : [{ name: "Landing" }],
      });
    } catch {
      // store error 셋팅
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <KeyboardAvoidingView
        className="flex-1"
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView
          contentContainerStyle={{ paddingHorizontal: 24, paddingTop: 24, paddingBottom: 40 }}
          keyboardShouldPersistTaps="handled"
        >
          <Text className="mb-2 font-serif text-2xl text-ink">회원가입</Text>
          <Text className="mb-8 font-sans text-sm text-ink-secondary">
            자평 사용을 위해 정보를 입력해주세요.
          </Text>

          <Field
            label="이메일"
            value={email}
            onChangeText={(v) => { setEmail(v); if (error) clearError(); }}
            placeholder="you@example.com"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="email"
            textContentType="emailAddress"
            returnKeyType="next"
            onSubmitEditing={() => passwordRef.current?.focus()}
            blurOnSubmit={false}
            error={!emailValid ? "올바른 이메일 형식이 아닙니다." : undefined}
            showError={touched.email && !emailValid && email.length > 0}
            testID="signup-email"
          />

          <Field
            ref={passwordRef}
            label="비밀번호 (8~72자)"
            value={password}
            onChangeText={(v) => { setPassword(v); if (error) clearError(); }}
            placeholder="••••••••"
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="password-new"
            textContentType="newPassword"
            returnKeyType="next"
            onSubmitEditing={() => passwordConfirmRef.current?.focus()}
            blurOnSubmit={false}
            error="비밀번호는 8~72자여야 합니다."
            showError={touched.password && !passwordValid && password.length > 0}
            testID="signup-password"
          />

          <Field
            ref={passwordConfirmRef}
            label="비밀번호 확인"
            value={passwordConfirm}
            onChangeText={setPasswordConfirm}
            placeholder="••••••••"
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="password-new"
            textContentType="newPassword"
            returnKeyType="next"
            error="비밀번호가 일치하지 않습니다."
            showError={touched.passwordConfirm && !passwordMatches && passwordConfirm.length > 0}
            testID="signup-password-confirm"
          />

          <Field
            label="이름 (선택)"
            value={name}
            onChangeText={setName}
            placeholder="홍길동"
            autoComplete="name"
            textContentType="name"
            returnKeyType="next"
          />

          <Field
            label="휴대폰 (선택, 알림용)"
            value={phone}
            onChangeText={setPhone}
            placeholder="010-1234-5678"
            keyboardType="number-pad"
            autoComplete="tel"
            textContentType="telephoneNumber"
            returnKeyType="done"
          />

          {/* 마케팅 동의 — 명시 opt-in. BM v2 다크패턴 차단. */}
          <Pressable
            accessibilityRole="checkbox"
            accessibilityLabel="마케팅 정보 수신 동의 (선택, 일진·할인 알림)"
            accessibilityHint="두 번 탭하여 토글"
            accessibilityState={{ checked: marketingConsent }}
            onPress={() => setMarketingConsent((v) => !v)}
            className="mt-2 mb-4 flex-row items-center"
          >
            <View
              className="mr-2 h-5 w-5 items-center justify-center rounded-md border"
              style={{
                borderColor: marketingConsent ? colors.gold.primary : colors.line,
                backgroundColor: marketingConsent ? colors.gold.primary : "transparent",
              }}
            >
              {marketingConsent ? (
                <Text style={{ color: colors.bg.base, fontWeight: "700", fontSize: 12 }}>
                  ✓
                </Text>
              ) : null}
            </View>
            <Text className="flex-1 font-sans text-sm text-ink-secondary">
              <Text className="text-ink">마케팅 정보 수신 (선택)</Text> — 일진·할인 알림. 언제든 해지.
            </Text>
          </Pressable>

          {error && (
            <View
              accessibilityLiveRegion="polite"
              className="mb-4 rounded-md border border-state-warning/40 bg-state-warning/10 px-3 py-2"
            >
              <Text className="font-sans text-sm text-state-warning">{error}</Text>
            </View>
          )}

          <Button
            label={loading ? "처리 중…" : "회원가입"}
            onPress={handleSubmit}
            loading={loading}
            disabled={!isFormValid}
            accessibilityLabel={loading ? "회원가입 처리 중" : "회원가입하기"}
            testID="signup-submit"
          />

          <Text className="mt-6 text-center font-sans text-[11px] leading-[16px] text-ink-faint">
            가입 시 <Text className="text-ink-muted">서비스 이용약관</Text>과{"\n"}
            <Text className="text-ink-muted">개인정보 처리방침</Text>에 동의한 것으로 봅니다.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

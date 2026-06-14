import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import type { RootStackParamList } from "@/navigation/types";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "Landing">;

// 첫 화면 미리보기 — '운세 결과'가 아니라 '결정 캘린더(도구)'를 보여준다.
const CAL_PREVIEW: { d: string; label: string; bg: string; dark?: boolean }[] = [
  { d: "월", label: "평", bg: colors.bg.card },
  { d: "화", label: "길", bg: "rgba(201,169,97,0.28)" },
  { d: "수", label: "대길", bg: "rgba(201,169,97,0.85)", dark: true },
  { d: "목", label: "평", bg: colors.bg.card },
  { d: "금", label: "주의", bg: "rgba(178,58,58,0.20)" },
  { d: "토", label: "길", bg: "rgba(201,169,97,0.28)" },
];

const PROOF_POINTS = ["결정론 엔진", "고전 출처", "운세 예측 아님"];

// 의사결정 도구 정체성 우선 — 決(결정)을 첫 번째로.
const FEATURES: { hanja: string; title: string; body: string }[] = [
  {
    hanja: "決",
    title: "운세가 아니라 결정",
    body: "이직·창업·결혼·이사 같은 큰 선택에서 'A냐 B냐'와 '언제 할까'를 검토합니다.",
  },
  {
    hanja: "算",
    title: "결과는 코드가 확정합니다",
    body: "절기·진태양시·60갑자를 결정론 엔진이 AI 밖에서 확정 — 같은 입력은 항상 같은 결과.",
  },
  {
    hanja: "據",
    title: "모든 해석에 고전 출처",
    body: "연해자평·삼명통회 등 원문 출처를 함께 표기해 근거를 추적할 수 있습니다.",
  },
];

export function LandingScreen() {
  const navigation = useNavigation<Nav>();

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <ScrollView contentContainerStyle={{ paddingBottom: 40 }}>
        <View className="px-5 pt-8">
          <View className="flex-row items-center justify-between">
            <View>
              <Text className="font-serif text-2xl text-ink">
                子<Text className="text-gold">平</Text>
              </Text>
              <Text className="mt-0.5 font-sans text-xs text-ink-muted">JAPYEONG</Text>
            </View>
            <View className="flex-row items-center gap-2">
              <Pressable
                accessibilityRole="button"
                onPress={() => {
                  // dynamic import 로 순환 의존 차단
                  const { useAuthStore } = require("@/stores/authStore");
                  const token = useAuthStore.getState().token;
                  navigation.navigate(token ? "Profile" : "AuthLanding");
                }}
                className="rounded-md border border-line bg-bg-card px-3 py-1.5 active:opacity-80"
              >
                <Text className="font-sans text-xs text-gold">내 계정</Text>
              </Pressable>
              <View className="rounded-md border border-line bg-bg-card px-3 py-1.5">
                <Text className="font-sans text-xs text-gold">의사결정 도구</Text>
              </View>
            </View>
          </View>

          {/* 히어로 — 의사결정 도구 정체성 */}
          <View className="pt-10 pb-7">
            <Text className="font-serif text-[42px] leading-[54px] text-ink">
              큰 결정,{"\n"}언제 할까?
            </Text>
            <Text className="mt-5 font-sans text-base leading-7 text-ink-secondary">
              이직·창업·결혼·이사처럼 되돌리기 어려운 선택 앞에서, A안과 B안을 같은
              기준으로 비교하고 결정의 시점을 검토하는 도구입니다. 운세 예측이 아니라,
              당신이 스스로 결정하도록 돕습니다.
            </Text>
          </View>

          {/* 미리보기 — 결정 캘린더(도구) */}
          <View className="rounded-lg border border-line bg-bg-elevated p-3">
            <View className="mb-3 flex-row items-center justify-between">
              <Text className="font-sans text-xs text-ink-muted">결정 캘린더 미리보기</Text>
              <Text className="font-sans text-xs text-gold">이 결정, 언제가 좋을까</Text>
            </View>
            <View className="flex-row gap-1.5">
              {CAL_PREVIEW.map((c, i) => (
                <View key={i} className="flex-1 items-center">
                  <Text className="mb-1 font-sans text-[10px] text-ink-muted">{c.d}</Text>
                  <View
                    className="w-full items-center justify-center rounded-md border"
                    style={{
                      aspectRatio: 1,
                      backgroundColor: c.bg,
                      borderColor: c.bg === colors.bg.card ? colors.line : "transparent",
                    }}
                  >
                    <Text
                      className="font-sans text-[10px] font-semibold"
                      style={{ color: c.dark ? "#0E0F13" : colors.text.secondary }}
                    >
                      {c.label}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
            <View className="mt-3 flex-row gap-2">
              {PROOF_POINTS.map((point) => (
                <View key={point} className="rounded-md border border-line bg-bg-raised px-2 py-1">
                  <Text className="font-sans text-[11px] text-ink-secondary">{point}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* 정체성 3카드 (決 우선) */}
          <View className="mt-5 gap-3">
            {FEATURES.map((f) => (
              <Card key={f.title} className="flex-row items-center gap-4">
                <View className="h-12 w-12 items-center justify-center rounded-lg border border-line bg-bg-card">
                  <Text className="font-serif text-2xl text-gold-light">{f.hanja}</Text>
                </View>
                <View className="flex-1">
                  <Text className="mb-1 font-serif text-base text-ink">{f.title}</Text>
                  <Text className="font-sans text-sm leading-6 text-ink-secondary">{f.body}</Text>
                </View>
              </Card>
            ))}
          </View>

          {/* 1차 CTA — 결정 타이밍 (시그니처) */}
          <View className="mt-10">
            <Pressable
              onPress={() => navigation.navigate("Timing")}
              className="flex-row items-center gap-3 rounded-lg border px-4 py-4 active:opacity-80"
              style={{ borderColor: colors.gold.primary, backgroundColor: "rgba(201,169,97,0.14)" }}
            >
              <Text className="font-serif text-3xl text-gold">決</Text>
              <View className="flex-1">
                <Text className="font-serif text-lg text-ink">결정 타이밍 보기</Text>
                <Text className="font-sans text-xs text-ink-secondary">
                  이 결정, 언제 할까 — 길흉 캘린더로 길일·피할 날
                </Text>
              </View>
              <Text className="font-sans text-lg text-gold">→</Text>
            </Pressable>

            {/* 2차 CTA — A vs B 결정 비교 */}
            <Pressable
              onPress={() => navigation.navigate("Decision")}
              className="mt-3 flex-row items-center gap-3 rounded-lg border border-line bg-bg-card px-4 py-4 active:opacity-80"
            >
              <Text className="font-serif text-2xl text-gold-light">⚖</Text>
              <View className="flex-1">
                <Text className="font-serif text-base text-ink">결정 도우미 · A vs B</Text>
                <Text className="font-sans text-xs text-ink-secondary">
                  두 갈림길을 같은 기준으로 비교
                </Text>
              </View>
              <Text className="font-sans text-lg text-gold-light">→</Text>
            </Pressable>

            {/* 보조 — 택일/궁합 */}
            <View className="mt-3 flex-row gap-2">
              <Pressable
                onPress={() => navigation.navigate("DateSelection")}
                className="flex-1 flex-row items-center justify-center gap-2 rounded-lg border border-line bg-bg-card py-3 active:opacity-80"
              >
                <Text className="font-serif text-base text-gold-light">擇日</Text>
                <Text className="font-sans text-xs text-ink-secondary">좋은 날</Text>
              </Pressable>
              <Pressable
                onPress={() => navigation.navigate("Compatibility")}
                className="flex-1 flex-row items-center justify-center gap-2 rounded-lg border border-line bg-bg-card py-3 active:opacity-80"
              >
                <Text className="font-serif text-base text-gold-light">宮合</Text>
                <Text className="font-sans text-xs text-ink-secondary">두 사람 비교</Text>
              </Pressable>
            </View>

            {/* 근거 데이터 — 명식 입력 강등 */}
            <View className="mt-6 border-t border-line pt-5">
              <Text className="mb-2 font-sans text-xs text-ink-muted">
                도구가 사용하는 근거 데이터
              </Text>
              <Pressable
                onPress={() => navigation.navigate("Onboarding")}
                className="flex-row items-center justify-between rounded-lg border border-line bg-bg-card px-4 py-3 active:opacity-80"
              >
                <Text className="font-sans text-sm text-ink-secondary">
                  내 명식 입력 · 보기 (생년월일 = 도구 설정)
                </Text>
                <Text className="font-sans text-base text-ink-muted">→</Text>
              </Pressable>
            </View>

            <Text className="mt-5 text-center font-sans text-xs text-ink-muted">
              자평은 의사결정 참고용 도구이며, 의학·법률·재무 판단을 대신하지 않습니다.
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import type { RootStackParamList } from "@/navigation/types";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "Landing">;

const PREVIEW_PILLARS = [
  { label: "년주", gan: "乙", ji: "丑", color: colors.ohaeng.mok },
  { label: "월주", gan: "丁", ji: "亥", color: colors.ohaeng.hwa },
  { label: "일주", gan: "丁", ji: "巳", color: colors.ohaeng.hwa, focus: true },
  { label: "시주", gan: "丁", ji: "未", color: colors.ohaeng.hwa },
];

const PROOF_POINTS = ["룰베이스 산출", "고전 근거", "잠정 표기"];

const FEATURES: { hanja: string; title: string; body: string }[] = [
  {
    hanja: "算",
    title: "사주는 AI가 계산하지 않습니다",
    body: "절기·60갑자·진태양시 보정은 결정론적 엔진이 먼저 확정합니다.",
  },
  {
    hanja: "據",
    title: "해석에는 근거가 붙습니다",
    body: "격국·용신·십성·합충을 분리해 보여 주고, 고전 출처와 학파 차이를 남깁니다.",
  },
  {
    hanja: "決",
    title: "운세보다 의사결정",
    body: "진로·관계·사업·시기 판단에 필요한 명리적 관점을 정리합니다.",
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
            <View className="rounded-md border border-line bg-bg-card px-3 py-1.5">
              <Text className="font-sans text-xs text-gold">명리 AI 자문</Text>
            </View>
          </View>

          <View className="pt-10 pb-7">
            <Text className="font-serif text-[42px] leading-[54px] text-ink">
              사주를{"\n"}전문가의 언어로.
            </Text>
            <Text className="mt-5 font-sans text-base leading-7 text-ink-secondary">
              자평은 명리 엔진이 원국을 확정하고, AI가 그 구조를 의사결정 자문으로
              번역하는 프리미엄 사주 서비스입니다.
            </Text>
          </View>

          <View className="rounded-lg border border-line bg-bg-elevated p-3">
            <View className="mb-3 flex-row items-center justify-between">
              <Text className="font-sans text-xs text-ink-muted">命式 PREVIEW</Text>
              <Text className="font-sans text-xs text-gold">丁火 일간</Text>
            </View>
            <View className="flex-row gap-2">
              {PREVIEW_PILLARS.map((p) => (
                <View
                  key={p.label}
                  className="flex-1 rounded-md border bg-bg-card px-2 py-3"
                  style={{
                    borderColor: p.focus ? "rgba(201,169,97,0.48)" : colors.line,
                    backgroundColor: p.focus ? "rgba(201,169,97,0.08)" : colors.bg.card,
                  }}
                >
                  <Text className="text-center font-sans text-[10px] text-ink-muted">
                    {p.label}
                  </Text>
                  <Text className="mt-2 text-center font-serif text-3xl" style={{ color: p.color }}>
                    {p.gan}
                  </Text>
                  <Text className="text-center font-serif text-3xl text-ink">{p.ji}</Text>
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

          <View className="mt-10">
            <Button label="명식 입력하기" onPress={() => navigation.navigate("Onboarding")} />

            {/* 부가 진입: 궁합 */}
            <View className="mt-3">
              <Pressable
                onPress={() => navigation.navigate("Compatibility")}
                className="flex-row items-center justify-center gap-2 rounded-lg border border-line bg-bg-card py-3 active:opacity-80"
              >
                <Text className="font-serif text-lg text-gold-light">宮合</Text>
                <Text className="font-sans text-sm text-ink-secondary">두 사주 궁합 보기</Text>
              </Pressable>
            </View>

            <Text className="mt-4 text-center font-sans text-xs text-ink-muted">
              자평은 의사결정 참고용 명리 자문이며, 의학·법률·재무 판단을 대신하지 않습니다.
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import type { RootStackParamList } from "@/navigation/types";

type Nav = NativeStackNavigationProp<RootStackParamList, "Landing">;

const FEATURES: { hanja: string; title: string; body: string }[] = [
  {
    hanja: "正",
    title: "정통 명리",
    body: "연해자평·자평진전 등 고전 알고리즘에 근거한 룰베이스 엔진이 사주 구조를 확정합니다.",
  },
  {
    hanja: "決",
    title: "의사결정 자문",
    body: "운세를 단정하는 점이 아니라, 진로·관계·시기 같은 결정을 돕는 차분한 자문입니다.",
  },
  {
    hanja: "精",
    title: "정밀한 사주",
    body: "진태양시 보정과 24절기 기반으로 년·월·일·시 여덟 글자를 정확히 산출합니다.",
  },
];

export function LandingScreen() {
  const navigation = useNavigation<Nav>();

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <ScrollView>
        <View className="px-5 pb-10">
          {/* 히어로 */}
          <View className="items-center pt-16 pb-10">
            <Text className="font-serif text-6xl text-gold">子平</Text>
            <Text className="mt-3 font-serif text-xl text-ink">자평 · 명리 AI 자문</Text>
            <Text className="mt-4 text-center font-sans text-base leading-7 text-ink-secondary">
              송나라 명리학자 서자평의 정신을 잇는{"\n"}
              명리학 기반 AI 의사결정 자문 서비스
            </Text>
          </View>

          {/* 특징 */}
          <View className="gap-3">
            {FEATURES.map((f) => (
              <Card key={f.title} className="flex-row items-center gap-4">
                <View className="h-12 w-12 items-center justify-center rounded-xl border border-line bg-bg-card">
                  <Text className="font-serif text-2xl text-gold-light">{f.hanja}</Text>
                </View>
                <View className="flex-1">
                  <Text className="mb-1 font-serif text-base text-ink">{f.title}</Text>
                  <Text className="font-sans text-sm leading-6 text-ink-secondary">{f.body}</Text>
                </View>
              </Card>
            ))}
          </View>

          {/* CTA */}
          <View className="mt-10">
            <Button label="서비스 시작하기" onPress={() => navigation.navigate("Onboarding")} />
            <Text className="mt-4 text-center font-sans text-xs text-ink-muted">
              사주 풀이는 의사결정 참고용 자문이며, 의학·법률·재무 판단을 대신하지 않습니다.
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { ActivityIndicator, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAnalyzeSaju } from "@/api/saju";
import type { TenGodsCount } from "@/api/types";
import { DaewoonList } from "@/components/domain/DaewoonList";
import { OhaengChart } from "@/components/domain/OhaengChart";
import { SajuGrid } from "@/components/domain/SajuGrid";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import type { RootStackParamList } from "@/navigation/types";
import { useBirthStore } from "@/stores/birthStore";

type Nav = NativeStackNavigationProp<RootStackParamList, "Saju">;

const TEN_GOD_LABEL: Record<keyof TenGodsCount, string> = {
  bi_gyeon: "비견",
  gyeop_jae: "겁재",
  sik_sin: "식신",
  sang_gwan: "상관",
  jeong_jae: "정재",
  pyeon_jae: "편재",
  jeong_gwan: "정관",
  pyeon_gwan: "편관",
  jeong_in: "정인",
  pyeon_in: "편인",
};

function SectionTitle({ children }: { children: string }) {
  return <Text className="mb-3 font-serif text-lg text-gold-light">{children}</Text>;
}

export function SajuScreen() {
  const birth = useBirthStore((s) => s.birth);
  const navigation = useNavigation<Nav>();
  const { data, isLoading, error } = useAnalyzeSaju(birth);

  if (!birth) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center bg-bg-base">
        <Text className="text-ink-secondary">출생 정보가 없습니다.</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView>
        <View className="gap-4 p-5">
          {isLoading && (
            <View className="items-center py-16">
              <ActivityIndicator color="#C9A961" />
              <Text className="mt-3 text-ink-muted">사주를 푸는 중…</Text>
            </View>
          )}

          {error && (
            <Card>
              <Text className="text-ohaeng-hwa">
                분석에 실패했습니다. 백엔드 서버 연결을 확인해 주세요.
              </Text>
              <Text className="mt-2 text-xs text-ink-muted">{String(error)}</Text>
            </Card>
          )}

          {data && (
            <>
              <Card>
                <SectionTitle>원국 (元局)</SectionTitle>
                <SajuGrid pillars={data.pillars} />
                <Text className="mt-4 text-center font-sans text-sm text-ink-secondary">
                  일간 {data.day_master} · {data.day_master_element}
                </Text>
              </Card>

              <Card>
                <SectionTitle>오행 분포</SectionTitle>
                <OhaengChart five={data.five_elements} />
                <Text className="mt-2 font-sans text-xs text-ink-muted">
                  최강 {data.five_elements.dominant} · 최약 {data.five_elements.weakest} · 균형{" "}
                  {(data.five_elements.balance * 100).toFixed(0)}%
                </Text>
              </Card>

              <Card>
                <SectionTitle>십성</SectionTitle>
                <View className="flex-row flex-wrap gap-2">
                  {(Object.keys(TEN_GOD_LABEL) as (keyof TenGodsCount)[])
                    .filter((k) => data.ten_gods[k] > 0)
                    .map((k) => (
                      <View
                        key={k}
                        className="rounded-full border border-line bg-bg-card px-3 py-1"
                      >
                        <Text className="font-sans text-sm text-ink">
                          {TEN_GOD_LABEL[k]} {data.ten_gods[k]}
                        </Text>
                      </View>
                    ))}
                </View>
              </Card>

              {data.relations.length > 0 && (
                <Card>
                  <SectionTitle>합·충·형·해·파</SectionTitle>
                  <View className="flex-row flex-wrap gap-2">
                    {data.relations.map((r, i) => (
                      <View
                        key={`${r.type}-${i}`}
                        className="rounded-full border border-line bg-bg-card px-3 py-1"
                      >
                        <Text className="font-serif text-sm text-ink">
                          {r.type} {r.members.join("")}
                        </Text>
                      </View>
                    ))}
                  </View>
                </Card>
              )}

              <Card>
                <SectionTitle>대운 (大運)</SectionTitle>
                <DaewoonList daewoon={data.daewoon} />
              </Card>

              {/* ⚠ 잠정(provisional) 섹션 — 자문위원 검증 전 */}
              <Card>
                <View className="mb-3 flex-row items-center justify-between">
                  <SectionTitle>강약·격국·용신</SectionTitle>
                  <View className="rounded-md border border-accent-brown bg-bg-card px-2 py-0.5">
                    <Text className="font-sans text-[10px] tracking-widest text-accent-clay">
                      잠정 · 자문위원 검증 전
                    </Text>
                  </View>
                </View>
                <View className="gap-3">
                  <View className="flex-row items-baseline gap-3">
                    <Text className="w-16 font-sans text-sm text-ink-muted">신강신약</Text>
                    <Text className="font-serif text-lg text-ink">{data.strength.label}</Text>
                    <Text className="font-sans text-xs text-ink-muted">
                      ({(data.strength.ally_ratio * 100).toFixed(0)}% 아군
                      {data.strength.deuk_ryeong ? " · 득령" : ""}
                      {data.strength.deuk_ji ? " · 득지" : ""})
                    </Text>
                  </View>
                  <View className="flex-row items-baseline gap-3">
                    <Text className="w-16 font-sans text-sm text-ink-muted">격국</Text>
                    <Text className="font-serif text-lg text-gold-light">{data.geokguk.name}</Text>
                    <Text className="font-sans text-xs text-ink-muted">
                      ({data.geokguk.based_on === "transparent" ? "투출" : "본기"} ·{" "}
                      {data.geokguk.based_gan})
                    </Text>
                  </View>
                  <View className="flex-row items-baseline gap-3">
                    <Text className="w-16 font-sans text-sm text-ink-muted">용신</Text>
                    <Text className="font-serif text-lg text-gold">{data.yongsin.yongsin}</Text>
                    <Text className="font-sans text-xs text-ink-muted">
                      희 {data.yongsin.huishin} · 기 {data.yongsin.gisin} · 구 {data.yongsin.gushin}
                    </Text>
                  </View>
                </View>
                <Text className="mt-3 font-sans text-[11px] leading-5 text-ink-muted">
                  본 결과는 통설 기반 자동 산출(잠정)입니다. 정통성 확정은 명리 자문위원
                  검증 케이스 수집 후 갱신됩니다.
                </Text>
              </Card>

              <View className="mt-2">
                <Button
                  label="AI 자문 시작하기 →"
                  onPress={() => navigation.navigate("Chat")}
                />
              </View>
            </>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

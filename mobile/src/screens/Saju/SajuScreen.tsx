import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { ActivityIndicator, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAnalyzeSaju } from "@/api/saju";
import type { TenGodsCount } from "@/api/types";
import { DaewoonList } from "@/components/domain/DaewoonList";
import { LifeFlowGraph } from "@/components/domain/LifeFlowGraph";
import { OhaengChart } from "@/components/domain/OhaengChart";
import { MiniSajuStrip, SajuGrid } from "@/components/domain/SajuGrid";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import type { RootStackParamList } from "@/navigation/types";
import { useBirthStore } from "@/stores/birthStore";
import { colors } from "@/theme";

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

function SectionTitle({ children, note }: { children: string; note?: string }) {
  return (
    <View className="mb-3 flex-row items-center justify-between">
      <Text className="font-serif text-lg text-gold-light">{children}</Text>
      {note ? <Text className="font-sans text-xs text-ink-muted">{note}</Text> : null}
    </View>
  );
}

// 신강신약 판정의 '확신도' — 판정 경계로부터 거리 기반(엔진 confidence).
// 정직한 불확실성 표면화: 경계 명조는 '해석 주의'로 솔직히 표기한다.
const CONFIDENCE_CHIP: Record<string, { label: string; text: string; border: string }> = {
  high: { label: "신뢰도 높음", text: "text-gold-light", border: "border-gold-muted" },
  medium: { label: "신뢰도 보통", text: "text-accent-clay", border: "border-accent-brown" },
  low: { label: "경계 · 해석 주의", text: "text-accent-terracotta", border: "border-accent-terracotta" },
};

const CONFIDENCE_FALLBACK = { label: "신뢰도 보통", text: "text-accent-clay", border: "border-accent-brown" };

function ConfidenceChip({ confidence }: { confidence?: string }) {
  const c = CONFIDENCE_CHIP[confidence ?? ""] ?? CONFIDENCE_FALLBACK;
  return (
    <View className={`rounded-md border ${c.border} bg-bg-card px-2 py-0.5`}>
      <Text className={`font-sans text-[10px] ${c.text}`}>{c.label}</Text>
    </View>
  );
}

export function SajuScreen() {
  const birth = useBirthStore((s) => s.birth);
  const navigation = useNavigation<Nav>();
  const { data, isLoading, error } = useAnalyzeSaju(birth);
  const tenGodEntries = data
    ? (Object.keys(TEN_GOD_LABEL) as (keyof TenGodsCount)[])
        .map((key) => ({ key, label: TEN_GOD_LABEL[key], value: data.ten_gods[key] }))
        .filter((item) => item.value > 0)
        .sort((a, b) => b.value - a.value)
    : [];

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
          {/* 재맥락화 — '운세 리포트'가 아니라 도구의 근거 데이터(엔진 출력) */}
          <View
            className="rounded-lg border bg-bg-elevated p-3"
            style={{ borderColor: colors.gold.muted }}
          >
            <View className="mb-1 flex-row items-center justify-between">
              <Text className="font-sans text-xs text-gold">근거 데이터</Text>
              <View className="rounded border border-line bg-bg-card px-1.5 py-0.5">
                <Text className="font-sans text-[10px] text-ink-secondary">결정론 엔진 · RULED</Text>
              </View>
            </View>
            <Text className="font-sans text-xs leading-5 text-ink-secondary">
              이 화면은 결정 타이밍·A/B 비교가 사용하는 근거 데이터입니다. 절기·진태양시·
              60갑자를 결정론 엔진이 AI 밖에서 확정합니다 — 같은 생년월일은 항상 같은 결과.
            </Text>
          </View>

          {isLoading && (
            <View className="items-center py-16">
              <ActivityIndicator color={colors.gold.primary} />
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
              <View className="rounded-lg border border-line bg-bg-card p-4">
                <View className="mb-4 flex-row items-start justify-between">
                  <View className="flex-1">
                    <Text className="font-serif text-3xl text-ink">
                      命式 <Text className="text-gold">분석</Text>
                    </Text>
                    <Text className="mt-2 font-sans text-sm leading-6 text-ink-secondary">
                      결정론적 명리 엔진이 확정한 원국을 기준으로 구조와 균형을 정리했습니다.
                    </Text>
                  </View>
                  <View className="rounded-md border border-lineStrong bg-bg-raised px-2.5 py-1">
                    <Text className="font-sans text-[11px] text-gold">RULED</Text>
                  </View>
                </View>
                <MiniSajuStrip pillars={data.pillars} />
                <View className="mt-4 flex-row gap-2">
                  <View className="flex-1 rounded-md border border-line bg-bg-elevated px-3 py-2">
                    <Text className="font-sans text-[11px] text-ink-muted">일간</Text>
                    <Text className="mt-1 font-serif text-lg text-gold-light">
                      {data.day_master}
                    </Text>
                  </View>
                  <View className="flex-1 rounded-md border border-line bg-bg-elevated px-3 py-2">
                    <Text className="font-sans text-[11px] text-ink-muted">오행</Text>
                    <Text className="mt-1 font-sans text-sm text-ink">
                      {data.day_master_element}
                    </Text>
                  </View>
                  <View className="flex-1 rounded-md border border-line bg-bg-elevated px-3 py-2">
                    <Text className="font-sans text-[11px] text-ink-muted">균형</Text>
                    <Text className="mt-1 font-sans text-sm text-ink">
                      {(data.five_elements.balance * 100).toFixed(0)}%
                    </Text>
                  </View>
                </View>
              </View>

              <Card>
                <SectionTitle note="4 pillars">원국 (元局)</SectionTitle>
                <SajuGrid pillars={data.pillars} />
                <Text className="mt-4 text-center font-sans text-sm text-ink-secondary">
                  일간 {data.day_master} · {data.day_master_element}
                </Text>
                {data.hour_estimated ? (
                  <Text className="mt-2 text-center font-sans text-[11px] leading-4 text-accent-clay">
                    시(時) 미상 — 정오 기준 추정. 시주·시간 십성 해석과 강약 신뢰도가 낮아집니다.
                  </Text>
                ) : null}
              </Card>

              <Card>
                <SectionTitle note="balance">오행 분포</SectionTitle>
                <OhaengChart five={data.five_elements} />
                <Text className="mt-2 font-sans text-xs text-ink-muted">
                  최강 {data.five_elements.dominant} · 최약 {data.five_elements.weakest} · 균형{" "}
                  {(data.five_elements.balance * 100).toFixed(0)}%
                </Text>
              </Card>

              <Card>
                <SectionTitle note="ten gods">십성</SectionTitle>
                <View className="flex-row flex-wrap gap-2">
                  {tenGodEntries.map((item) => (
                    <View
                      key={item.key}
                      className="rounded-md border border-line bg-bg-card px-3 py-1.5"
                    >
                      <Text className="font-sans text-sm text-ink">
                        {item.label} {item.value}
                      </Text>
                    </View>
                  ))}
                </View>
              </Card>

              {data.relations.length > 0 && (
                <Card>
                  <SectionTitle note="relations">합·충·형·해·파</SectionTitle>
                  <View className="flex-row flex-wrap gap-2">
                    {data.relations.map((r, i) => (
                      <View
                        key={`${r.type}-${i}`}
                        className="rounded-md border border-line bg-bg-card px-3 py-1.5"
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
                <SectionTitle note="10-year flow">대운 (大運)</SectionTitle>
                <DaewoonList daewoon={data.daewoon} />
              </Card>

              {/* 인생 흐름 그래프 — 잠정 */}
              {data.life_flow.length > 0 && (
                <Card>
                  <View className="mb-3 flex-row items-center justify-between">
                    <Text className="font-serif text-lg text-gold-light">
                      인생 흐름 (人生流)
                    </Text>
                    <View className="rounded-md border border-accent-brown bg-bg-card px-2 py-0.5">
                      <Text className="font-sans text-[10px] text-accent-clay">
                        잠정 · 자문위원 검증 전
                      </Text>
                    </View>
                  </View>
                  <LifeFlowGraph points={data.life_flow} />
                </Card>
              )}

              <Card>
                <View className="mb-3 flex-row items-center justify-between">
                  <Text className="font-serif text-lg text-gold-light">강약·격국·용신</Text>
                  <View className="rounded-md border border-accent-brown bg-bg-card px-2 py-0.5">
                    <Text className="font-sans text-[10px] text-ink-secondary">
                      전통명리 결정론 엔진
                    </Text>
                  </View>
                </View>
                <View className="gap-3">
                  <View className="flex-row items-center gap-3">
                    <Text className="w-16 font-sans text-sm text-ink-muted">신강신약</Text>
                    <Text className="font-serif text-lg text-ink">{data.strength.label}</Text>
                    <Text className="font-sans text-xs text-ink-muted">
                      ({(data.strength.ally_ratio * 100).toFixed(0)}% 아군
                      {data.strength.deuk_ryeong ? " · 득령" : ""}
                      {data.strength.deuk_ji ? " · 득지" : ""})
                    </Text>
                    <ConfidenceChip confidence={data.strength.confidence} />
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
                  신강신약은 학술파 계분법(월령 본기 가중)으로 산출하며, 고전 통설
                  검증셋과 일치하도록 보정되었습니다. 격국·용신은 통설 기반 방향 제시이며,
                  극단격(전왕·종격)은 AI 자문으로 보완됩니다.
                </Text>
              </Card>

              <View className="mt-2 gap-2">
                <Button
                  label="AI 자문 시작하기"
                  onPress={() => navigation.navigate("Chat")}
                />
                <Button
                  label="궁합 보기 (두 사주 비교)"
                  variant="ghost"
                  onPress={() => navigation.navigate("Compatibility")}
                />
                <Button
                  label="택일 (좋은 날 찾기)"
                  variant="ghost"
                  onPress={() => navigation.navigate("DateSelection")}
                />
                <Button
                  label="결정 도우미 (A vs B)"
                  variant="ghost"
                  onPress={() => navigation.navigate("Decision")}
                />
              </View>
            </>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

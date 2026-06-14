/**
 * 무료 리딩 카드 — 전환 퍼널 1단계.
 *
 * 저장된 명식이 있으면 /v1/chat/teaser 로 '내 한 줄'(결정론, 무료·즉시)을 보여 주고,
 * 전체 풀이(LLM)는 코인/구독으로 잠근다. 명식이 없으면 '무료로 받기' CTA.
 * 공포·단정 톤 없음 — 정확한 성향/흐름 + 정직한 잠금.
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useQuery } from "@tanstack/react-query";
import { ActivityIndicator, Pressable, Text, View } from "react-native";

import { fetchTeaser } from "@/api/chat";
import { HanjaText } from "@/components/primitives/HanjaText";
import type { RootStackParamList } from "@/navigation/types";
import { useBirthStore } from "@/stores/birthStore";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "Landing">;

export function TeaserCard() {
  const navigation = useNavigation<Nav>();
  const birth = useBirthStore((s) => s.birth);

  const q = useQuery({
    queryKey: ["teaser", birth?.year, birth?.month, birth?.day, birth?.hour],
    queryFn: () => fetchTeaser({ birth: birth! }),
    enabled: !!birth,
    staleTime: 1000 * 60 * 60 * 12,
  });

  // 명식 미입력 — 무료 받기 유도
  if (!birth) {
    return (
      <Pressable
        onPress={() => navigation.navigate("Onboarding")}
        className="rounded-xl border bg-bg-elevated p-4 active:opacity-80"
        style={{ borderColor: colors.gold.muted }}
      >
        <Text className="font-serif text-base text-gold">무료로 내 한 줄 받기</Text>
        <Text className="mt-1 font-sans text-sm text-ink-secondary">
          생년월일만 넣으면, 내 명식의 핵심을 한 줄로 — 무료.
        </Text>
      </Pressable>
    );
  }

  return (
    <View className="rounded-xl border bg-bg-elevated p-4" style={{ borderColor: colors.gold.muted }}>
      <View className="mb-2 flex-row items-center justify-between">
        <Text className="font-sans text-xs text-ink-muted">오늘의 내 한 줄 · 무료</Text>
        <Text className="font-sans text-[10px] text-gold">결정론 명식</Text>
      </View>

      {q.isPending ? (
        <View className="py-3">
          <ActivityIndicator color={colors.gold.primary} />
        </View>
      ) : q.isError ? (
        <Text className="font-sans text-sm text-ink-secondary">
          잠시 후 다시 시도해 주세요.
        </Text>
      ) : q.data ? (
        <>
          <HanjaText className="font-serif text-base leading-7 text-ink">
            {q.data.hook}
          </HanjaText>
          {!!q.data.flow && (
            <HanjaText className="mt-1 font-sans text-sm leading-6 text-gold-light">
              {q.data.flow}
            </HanjaText>
          )}

          {/* 잠긴 전체 풀이 — 궁금증 → 결제 */}
          <View className="mt-3 rounded-lg border border-line bg-bg-card p-3">
            <Text className="mb-1 font-sans text-xs text-ink-muted">
              🔒 전체 풀이에서 짚어 드려요
            </Text>
            {q.data.covers.slice(0, 3).map((c, i) => (
              <Text key={i} className="font-sans text-sm leading-6 text-ink-secondary">
                · {c}
              </Text>
            ))}
          </View>

          <View className="mt-3 gap-2">
            <Pressable
              onPress={() => navigation.navigate("Chat")}
              className="items-center rounded-lg border py-3 active:opacity-80"
              style={{ borderColor: colors.gold.primary, backgroundColor: "rgba(201,169,97,0.14)" }}
            >
              <Text className="font-serif text-sm text-gold">전체 풀이 보기</Text>
            </Pressable>
            <Pressable
              onPress={() => navigation.navigate("Coins")}
              className="items-center py-1.5 active:opacity-70"
            >
              <Text className="font-sans text-xs text-ink-muted">
                심층 풀이 잠금 해제 · 코인 {q.data.unlock.coin_cost.toLocaleString("ko-KR")}~
              </Text>
            </Pressable>
          </View>
        </>
      ) : null}
    </View>
  );
}

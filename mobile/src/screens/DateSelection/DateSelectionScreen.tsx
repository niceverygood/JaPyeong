/**
 * 택일(擇日) 화면 — 사용자 사주 + 기간 + 행사 유형 → 좋은 날 Top N.
 *
 * MVP:
 *  - 행사 유형 4개 카드 (결혼/이주/사업/계약) + general
 *  - 시작·종료 날짜 (YYYY-MM-DD 텍스트 입력)
 *  - 결과 카드: 날짜·일진·점수·라벨·사유
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useDateSelection, type EventType } from "@/api/dateSelection";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Field } from "@/components/primitives/Field";
import { HanjaText } from "@/components/primitives/HanjaText";
import type { RootStackParamList } from "@/navigation/types";
import { useBirthStore } from "@/stores/birthStore";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "DateSelection">;

const EVENTS: { value: EventType; label: string; hanja: string; desc: string }[] = [
  { value: "marriage", label: "결혼", hanja: "婚", desc: "혼례·약혼·상견례" },
  { value: "moving", label: "이주", hanja: "移", desc: "이사·해외 이전" },
  { value: "business", label: "사업", hanja: "業", desc: "개업·창업·계약 체결" },
  { value: "contract", label: "계약", hanja: "契", desc: "중요 서명·법적 계약" },
  { value: "general", label: "일반", hanja: "凡", desc: "특별 행사 없이 길일" },
];

function labelTextColor(label: string): string {
  switch (label) {
    case "대길":
      return colors.gold.primary;
    case "길":
      return colors.gold.light;
    case "주의":
      return colors.ohaeng.hwa;
    case "흉":
      return colors.ohaeng.hwa;
    default:
      return colors.text.secondary;
  }
}

function todayIso(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function DateSelectionScreen() {
  const birth = useBirthStore((s) => s.birth);
  const navigation = useNavigation<Nav>();
  const mutation = useDateSelection();

  const [event, setEvent] = useState<EventType>("marriage");
  const [start, setStart] = useState<string>(todayIso(0));
  const [end, setEnd] = useState<string>(todayIso(60));
  const [topN, setTopN] = useState<string>("7");
  const [error, setError] = useState<string | null>(null);

  if (!birth) {
    return (
      <SafeAreaView className="flex-1 bg-bg-base p-6">
        <Text className="mb-4 font-serif text-2xl text-ink">택일 (擇日)</Text>
        <Text className="mb-4 font-sans text-sm text-ink-secondary">
          좋은 날을 찾으려면 먼저 본인의 명식이 필요합니다.
        </Text>
        <Button
          label="명식 입력하기"
          onPress={() => navigation.navigate("Onboarding")}
        />
      </SafeAreaView>
    );
  }

  const submit = () => {
    if (!DATE_RE.test(start) || !DATE_RE.test(end)) {
      setError("날짜는 YYYY-MM-DD 형식으로 입력해 주세요.");
      return;
    }
    if (new Date(end) < new Date(start)) {
      setError("종료일이 시작일보다 앞섭니다.");
      return;
    }
    const n = Number(topN) || 7;
    setError(null);
    mutation.mutate({
      birth,
      start,
      end,
      event_type: event,
      top_n: Math.max(1, Math.min(30, n)),
    });
  };

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView keyboardShouldPersistTaps="handled">
        <View className="p-5 pb-10">
          {/* 헤더 */}
          <View className="mb-4">
            <Text className="font-serif text-3xl text-ink">
              擇日 <Text className="text-gold">택일</Text>
            </Text>
            <Text className="mt-1 font-sans text-sm text-ink-secondary">
              본인의 사주를 기준으로 기간 안의 좋은 날을 찾습니다.
            </Text>
          </View>

          {/* 행사 유형 */}
          <Text className="mb-2 font-sans text-sm text-ink-secondary">행사 유형</Text>
          <View className="mb-4 flex-row flex-wrap gap-2">
            {EVENTS.map((e) => {
              const active = event === e.value;
              return (
                <Pressable
                  key={e.value}
                  onPress={() => setEvent(e.value)}
                  className="rounded-lg border px-3 py-2.5"
                  style={{
                    width: "31%",
                    backgroundColor: active ? "rgba(201,169,97,0.10)" : colors.bg.card,
                    borderColor: active ? colors.gold.primary : colors.line,
                  }}
                >
                  <View className="flex-row items-baseline gap-1.5">
                    <Text
                      className={`font-serif text-lg ${active ? "text-gold" : "text-gold-light"}`}
                    >
                      {e.hanja}
                    </Text>
                    <Text
                      className={`font-sans text-sm ${active ? "text-ink" : "text-ink-secondary"}`}
                    >
                      {e.label}
                    </Text>
                  </View>
                  <Text className="mt-0.5 font-sans text-[10px] text-ink-muted">
                    {e.desc}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* 기간 */}
          <View className="flex-row gap-2">
            <View className="flex-1">
              <Field
                label="시작일 (YYYY-MM-DD)"
                value={start}
                onChangeText={setStart}
                placeholder="2026-05-27"
              />
            </View>
            <View className="flex-1">
              <Field
                label="종료일"
                value={end}
                onChangeText={setEnd}
                placeholder="2026-07-27"
              />
            </View>
          </View>

          <Field
            label="추천 개수 (1~30)"
            value={topN}
            onChangeText={setTopN}
            placeholder="7"
            keyboardType="number-pad"
          />

          {error && (
            <Text className="mb-3 font-sans text-sm text-ohaeng-hwa">{error}</Text>
          )}

          <Button
            label={mutation.isPending ? "찾는 중…" : "좋은 날 찾기"}
            onPress={submit}
            disabled={mutation.isPending}
          />

          {mutation.isPending && (
            <View className="mt-4 flex-row items-center justify-center gap-2">
              <ActivityIndicator color={colors.gold.primary} />
              <Text className="font-sans text-sm text-ink-secondary">
                기간 내 모든 날을 점수화 중…
              </Text>
            </View>
          )}

          {mutation.isError && (
            <View className="mt-4 rounded-lg border border-accent-brown bg-bg-card p-3">
              <Text className="font-sans text-sm text-ohaeng-hwa">
                택일 결과를 불러오지 못했습니다.
              </Text>
              <Text className="mt-1 font-sans text-xs text-ink-muted">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : String(mutation.error)}
              </Text>
            </View>
          )}

          {mutation.data && (
            <View className="mt-4 gap-2">
              <Text className="font-sans text-xs text-ink-muted">
                상위 {mutation.data.candidates.length}건 · 점수 내림차순
              </Text>
              {mutation.data.candidates.map((c) => (
                <Card key={c.date}>
                  <View className="flex-row items-baseline justify-between">
                    <Text className="font-serif text-base text-ink">{c.date}</Text>
                    <Text
                      className="font-sans text-sm"
                      style={{ color: labelTextColor(c.label) }}
                    >
                      {c.label} ({c.score >= 0 ? "+" : ""}
                      {c.score.toFixed(1)})
                    </Text>
                  </View>
                  <HanjaText className="mt-1 font-serif text-sm text-gold-light">
                    {`일진 ${c.day_pillar.gan}${c.day_pillar.ji} · 일운(${c.ten_god})`}
                  </HanjaText>
                  {c.reasons.length > 0 && (
                    <View className="mt-2">
                      {c.reasons.map((r, i) => (
                        <HanjaText
                          key={i}
                          className="font-sans text-xs leading-5 text-ink-secondary"
                        >
                          {`· ${r}`}
                        </HanjaText>
                      ))}
                    </View>
                  )}
                </Card>
              ))}
              <Text className="mt-2 px-2 text-center font-sans text-[10px] text-ink-muted">
                {mutation.data.note}
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

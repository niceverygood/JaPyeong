/**
 * 결정 타이밍 코치 — 자평 시그니처 화면.
 *
 * "이 결정을 언제?" 에 답한다. 이벤트 유형 + 기간 → 명식 대비 길흉 캘린더 히트맵
 * + 추천 길일/피할 날 + AI 코치 내러티브(고전 인용). 점신·포스텔러에 없는 '결정' 카테고리.
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import type { CandidateDate, EventType } from "@/api/timing";
import { useTiming } from "@/api/timing";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Field } from "@/components/primitives/Field";
import { HanjaText } from "@/components/primitives/HanjaText";
import type { RootStackParamList } from "@/navigation/types";
import { useBirthStore } from "@/stores/birthStore";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "Timing">;

const EVENTS: { value: EventType; label: string; hanja: string }[] = [
  { value: "marriage", label: "결혼", hanja: "婚" },
  { value: "moving", label: "이사", hanja: "移" },
  { value: "business", label: "개업", hanja: "業" },
  { value: "contract", label: "계약", hanja: "契" },
  { value: "general", label: "일반", hanja: "凡" },
];

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

function isoOffset(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** label → 히트맵 셀 색. 대길/길=금색 농담, 평=중립, 주의/흉=화(적). */
function cellStyle(label: string): { bg: string; border: string; text: string } {
  switch (label) {
    case "대길":
      return { bg: "rgba(201,169,97,0.85)", border: colors.gold.primary, text: "#0E0F13" };
    case "길":
      return { bg: "rgba(201,169,97,0.28)", border: colors.gold.primary, text: colors.gold.light };
    case "주의":
      return { bg: "rgba(178,58,58,0.18)", border: colors.ohaeng.hwa, text: colors.ohaeng.hwa };
    case "흉":
      return { bg: "rgba(178,58,58,0.38)", border: colors.ohaeng.hwa, text: "#F2D6D6" };
    default:
      return { bg: colors.bg.card, border: colors.line, text: colors.text.secondary };
  }
}

function labelTextColor(label: string): string {
  if (label === "대길") return colors.gold.primary;
  if (label === "길") return colors.gold.light;
  if (label === "주의" || label === "흉") return colors.ohaeng.hwa;
  return colors.text.secondary;
}

interface MonthGrid {
  key: string; // YYYY-MM
  title: string; // YYYY.MM
  leading: number; // 1일의 요일(0=일)
  days: { day: number; iso: string; cand: CandidateDate | null }[];
}

function buildMonths(calendar: CandidateDate[]): MonthGrid[] {
  const byDate = new Map(calendar.map((c) => [c.date, c]));
  const monthKeys: string[] = [];
  for (const c of calendar) {
    const mk = c.date.slice(0, 7);
    if (!monthKeys.includes(mk)) monthKeys.push(mk);
  }
  return monthKeys.map((mk) => {
    const parts = mk.split("-");
    const y = Number(parts[0]);
    const m = Number(parts[1]);
    const daysInMonth = new Date(y, m, 0).getDate();
    const leading = new Date(y, m - 1, 1).getDay();
    const days = [];
    for (let d = 1; d <= daysInMonth; d++) {
      const iso = `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      days.push({ day: d, iso, cand: byDate.get(iso) ?? null });
    }
    return { key: mk, title: `${y}.${String(m).padStart(2, "0")}`, leading, days };
  });
}

export function TimingScreen() {
  const birth = useBirthStore((s) => s.birth);
  const navigation = useNavigation<Nav>();
  const mutation = useTiming();

  const [event, setEvent] = useState<EventType>("marriage");
  const [start, setStart] = useState(isoOffset(0));
  const [end, setEnd] = useState(isoOffset(45));
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CandidateDate | null>(null);

  const months = useMemo(
    () => (mutation.data ? buildMonths(mutation.data.calendar) : []),
    [mutation.data],
  );

  if (!birth) {
    return (
      <SafeAreaView className="flex-1 bg-bg-base p-6">
        <Text className="mb-2 font-serif text-2xl text-ink">결정 타이밍 코치</Text>
        <Text className="mb-4 font-sans text-sm text-ink-secondary">
          언제 실행할지 보려면 먼저 본인의 명식이 필요합니다.
        </Text>
        <Button label="명식 입력하기" onPress={() => navigation.navigate("Onboarding")} />
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
    const span = (new Date(end).getTime() - new Date(start).getTime()) / 86400000;
    if (span > 92) {
      setError("기간은 최대 92일(약 3개월)까지 볼 수 있습니다.");
      return;
    }
    setError(null);
    setSelected(null);
    mutation.mutate({ birth, start, end, event_type: event, top_n: 5 });
  };

  const data = mutation.data;

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView keyboardShouldPersistTaps="handled">
        <View className="p-5 pb-12">
          <View className="mb-4">
            <Text className="font-serif text-3xl text-ink">
              決 <Text className="text-gold">결정 타이밍</Text>
            </Text>
            <Text className="mt-1 font-sans text-sm text-ink-secondary">
              "이 결정을 언제 할까" — 명식 흐름으로 길일과 피할 날을 짚어 드립니다.
            </Text>
          </View>

          {/* 이벤트 유형 */}
          <Text className="mb-2 font-sans text-sm text-ink-secondary">무엇을 정하시나요?</Text>
          <View className="mb-4 flex-row flex-wrap gap-2">
            {EVENTS.map((e) => {
              const active = event === e.value;
              return (
                <Pressable
                  key={e.value}
                  onPress={() => setEvent(e.value)}
                  className="flex-row items-baseline gap-1.5 rounded-lg border px-3 py-2.5"
                  style={{
                    backgroundColor: active ? "rgba(201,169,97,0.10)" : colors.bg.card,
                    borderColor: active ? colors.gold.primary : colors.line,
                  }}
                >
                  <Text className={`font-serif text-lg ${active ? "text-gold" : "text-gold-light"}`}>
                    {e.hanja}
                  </Text>
                  <Text className={`font-sans text-sm ${active ? "text-ink" : "text-ink-secondary"}`}>
                    {e.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* 기간 */}
          <View className="flex-row gap-2">
            <View className="flex-1">
              <Field label="시작일" value={start} onChangeText={setStart} placeholder="2026-06-14" />
            </View>
            <View className="flex-1">
              <Field label="종료일 (최대 3개월)" value={end} onChangeText={setEnd} placeholder="2026-07-29" />
            </View>
          </View>

          {error && <Text className="mb-3 font-sans text-sm text-ohaeng-hwa">{error}</Text>}

          <Button
            label={mutation.isPending ? "흐름을 읽는 중…" : "타이밍 분석"}
            onPress={submit}
            disabled={mutation.isPending}
          />

          {mutation.isPending && (
            <View className="mt-4 flex-row items-center justify-center gap-2">
              <ActivityIndicator color={colors.gold.primary} />
              <Text className="font-sans text-sm text-ink-secondary">
                기간 내 모든 날을 명식과 대조 중…
              </Text>
            </View>
          )}

          {mutation.isError && (
            <View className="mt-4 rounded-lg border border-accent-brown bg-bg-card p-3">
              <Text className="font-sans text-sm text-ohaeng-hwa">분석을 불러오지 못했습니다.</Text>
              <Text className="mt-1 font-sans text-xs text-ink-muted">
                {mutation.error instanceof Error ? mutation.error.message : String(mutation.error)}
              </Text>
            </View>
          )}

          {data && (
            <View className="mt-5 gap-4">
              {/* AI 코치 내러티브 */}
              {data.recommendation ? (
                <Card>
                  <View className="p-1">
                    <View className="mb-2 flex-row items-center justify-between">
                      <Text className="font-serif text-lg text-gold">코치의 제안</Text>
                      {data.model.includes("opus") && (
                        <View
                          className="rounded-full border px-2 py-0.5"
                          style={{ borderColor: colors.gold.muted }}
                        >
                          <Text className="font-sans text-[10px] text-gold-light">심층 분석</Text>
                        </View>
                      )}
                    </View>
                    <HanjaText className="font-sans text-sm leading-6 text-ink">
                      {data.recommendation}
                    </HanjaText>
                    {!!data.timing && (
                      <HanjaText className="mt-2 font-sans text-xs leading-5 text-gold-light">
                        {`⏱ ${data.timing}`}
                      </HanjaText>
                    )}
                    {data.citations.length > 0 && (
                      <View className="mt-3 flex-row flex-wrap gap-1.5">
                        {data.citations.map((c, i) => (
                          <View key={i} className="rounded border border-line bg-bg-elevated px-2 py-0.5">
                            <HanjaText className="font-sans text-[10px] text-ink-secondary">
                              {c.volume ? `${c.source} ${c.volume}` : c.source}
                            </HanjaText>
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                </Card>
              ) : null}

              {/* 캘린더 히트맵 (넓은 화면에서 셀 과대 방지 — 모바일 폭 기준 유지) */}
              <View style={{ width: "100%", maxWidth: 460, alignSelf: "center" }}>
                <Text className="mb-2 font-sans text-sm text-ink-secondary">길흉 캘린더</Text>
                {months.map((mo) => (
                  <View key={mo.key} className="mb-4">
                    <Text className="mb-1 font-serif text-sm text-ink">{mo.title}</Text>
                    <View className="flex-row">
                      {WEEKDAYS.map((w, i) => (
                        <Text
                          key={w}
                          className="text-center font-sans text-[10px] text-ink-muted"
                          style={{ width: `${100 / 7}%`, color: i === 0 ? colors.ohaeng.hwa : colors.text.muted }}
                        >
                          {w}
                        </Text>
                      ))}
                    </View>
                    <View className="flex-row flex-wrap">
                      {Array.from({ length: mo.leading }).map((_, i) => (
                        <View key={`b${i}`} style={{ width: `${100 / 7}%`, aspectRatio: 1 }} />
                      ))}
                      {mo.days.map((d) => {
                        if (!d.cand) {
                          return (
                            <View key={d.iso} style={{ width: `${100 / 7}%`, aspectRatio: 1, padding: 2 }}>
                              <View className="flex-1 items-center justify-center rounded-md" style={{ backgroundColor: "transparent" }}>
                                <Text className="font-sans text-[11px] text-ink-faint">{d.day}</Text>
                              </View>
                            </View>
                          );
                        }
                        const st = cellStyle(d.cand.label);
                        const isSel = selected?.date === d.iso;
                        return (
                          <View key={d.iso} style={{ width: `${100 / 7}%`, aspectRatio: 1, padding: 2 }}>
                            <Pressable
                              onPress={() => setSelected(d.cand)}
                              className="flex-1 items-center justify-center rounded-md border"
                              style={{
                                backgroundColor: st.bg,
                                borderColor: isSel ? colors.text.primary : st.border,
                                borderWidth: isSel ? 2 : 1,
                              }}
                            >
                              <Text className="font-sans text-[11px] font-semibold" style={{ color: st.text }}>
                                {d.day}
                              </Text>
                            </Pressable>
                          </View>
                        );
                      })}
                    </View>
                  </View>
                ))}
                {/* 범례 */}
                <View className="flex-row flex-wrap gap-3">
                  {["대길", "길", "주의", "흉"].map((l) => {
                    const st = cellStyle(l);
                    return (
                      <View key={l} className="flex-row items-center gap-1">
                        <View className="h-3 w-3 rounded-sm border" style={{ backgroundColor: st.bg, borderColor: st.border }} />
                        <Text className="font-sans text-[10px] text-ink-muted">{l}</Text>
                      </View>
                    );
                  })}
                </View>
              </View>

              {/* 선택한 날 상세 */}
              {selected && (
                <Card>
                  <View className="flex-row items-baseline justify-between">
                    <Text className="font-serif text-base text-ink">{selected.date}</Text>
                    <Text className="font-sans text-sm" style={{ color: labelTextColor(selected.label) }}>
                      {selected.label} ({selected.score >= 0 ? "+" : ""}
                      {selected.score.toFixed(1)})
                    </Text>
                  </View>
                  <HanjaText className="mt-1 font-serif text-sm text-gold-light">
                    {`일진 ${selected.day_pillar.gan}${selected.day_pillar.ji} · 일운(${selected.ten_god})`}
                  </HanjaText>
                  {selected.reasons.map((r, i) => (
                    <HanjaText key={i} className="mt-1 font-sans text-xs leading-5 text-ink-secondary">
                      {`· ${r}`}
                    </HanjaText>
                  ))}
                </Card>
              )}

              {/* 추천 길일 */}
              {data.best.length > 0 && (
                <View>
                  <Text className="mb-2 font-sans text-sm text-gold">추천 길일</Text>
                  <View className="gap-2">
                    {data.best.map((c) => (
                      <Pressable key={c.date} onPress={() => setSelected(c)}>
                        <Card>
                          <View className="flex-row items-baseline justify-between">
                            <Text className="font-serif text-base text-ink">{c.date}</Text>
                            <Text className="font-sans text-sm text-gold">
                              {c.label} (+{c.score.toFixed(1)})
                            </Text>
                          </View>
                          <HanjaText className="mt-1 font-sans text-xs text-ink-secondary">
                            {`${c.day_pillar.gan}${c.day_pillar.ji} · ${c.reasons.slice(0, 2).join(" · ")}`}
                          </HanjaText>
                        </Card>
                      </Pressable>
                    ))}
                  </View>
                </View>
              )}

              {/* 피할 날 */}
              {data.avoid.length > 0 && (
                <View>
                  <Text className="mb-2 font-sans text-sm text-ohaeng-hwa">피하면 좋은 날</Text>
                  <View className="gap-2">
                    {data.avoid.map((c) => (
                      <Pressable key={c.date} onPress={() => setSelected(c)}>
                        <Card>
                          <View className="flex-row items-baseline justify-between">
                            <Text className="font-serif text-base text-ink">{c.date}</Text>
                            <Text className="font-sans text-sm" style={{ color: colors.ohaeng.hwa }}>
                              {c.label} ({c.score.toFixed(1)})
                            </Text>
                          </View>
                          <HanjaText className="mt-1 font-sans text-xs text-ink-secondary">
                            {`${c.day_pillar.gan}${c.day_pillar.ji} · ${c.reasons.slice(0, 2).join(" · ")}`}
                          </HanjaText>
                        </Card>
                      </Pressable>
                    ))}
                  </View>
                </View>
              )}

              <Text className="px-2 text-center font-sans text-[10px] leading-4 text-ink-muted">
                {data.note}
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

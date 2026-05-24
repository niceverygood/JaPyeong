import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useChat, type ChatResponse } from "@/api/chat";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useBirthStore } from "@/stores/birthStore";

interface Category {
  hanja: string;
  label: string;
  prompt: string;
}

// 12개 한자 카드 — 누르면 그 sector 전용 사주풀이가 단일 결과 패널로 표시.
const CATEGORIES: Category[] = [
  {
    hanja: "職",
    label: "진로·직업",
    prompt:
      "진로와 직업 방향을 사주 관점에서 짚어 주세요. 관성과 식상의 흐름, 격국·용신 관점에서 어떤 분야가 어울리는지 알려 주세요.",
  },
  {
    hanja: "業",
    label: "사업·창업",
    prompt:
      "사업과 창업의 시기·방향을 짚어 주세요. 재성과 식상의 흐름, 대운에서 유리한 구간과 주의해야 할 시기를 알려 주세요.",
  },
  {
    hanja: "財",
    label: "재정·투자",
    prompt:
      "재정 운영과 투자 관점에서 봐 주세요. 재성의 강약과 위치, 보존과 확장 사이의 비율, 주의 시기를 짚어 주세요.",
  },
  {
    hanja: "緣",
    label: "연애·인연",
    prompt:
      "연애와 인연의 흐름을 사주 관점에서 봐 주세요. 배우자성·합·충·도화·홍염 같은 신호와 앞으로의 흐름을 짚어 주세요.",
  },
  {
    hanja: "婚",
    label: "결혼·배우자",
    prompt:
      "결혼 적기와 배우자 관점에서 봐 주세요. 일주의 배우자성·합·충·형, 대운에서 결혼에 부합하는 시기와 배우자의 결을 짚어 주세요.",
  },
  {
    hanja: "子",
    label: "자녀·출산",
    prompt:
      "자녀운과 출산 시기, 자녀와의 관계를 봐 주세요. 식상(여)·관성(남)의 흐름과 자녀 자리 신호를 짚어 주세요.",
  },
  {
    hanja: "家",
    label: "가족 관계",
    prompt:
      "가족 관계를 사주 관점에서 봐 주세요. 부모성·형제성·세대 간 흐름과 가족 안에서의 역할을 짚어 주세요.",
  },
  {
    hanja: "體",
    label: "건강·체력",
    prompt:
      "오행 균형 관점에서 건강과 체력 신호를 봐 주세요. 약한 오행·강한 오행·대운에서 주의할 시기를 알려 주세요. (의학적 진단이 아닌 명리적 관점)",
  },
  {
    hanja: "學",
    label: "학업·시험",
    prompt:
      "학업·시험·자격증 관점에서 봐 주세요. 인성의 강약과 식상 흐름, 대운에서 학업·시험에 유리한 시기를 짚어 주세요.",
  },
  {
    hanja: "移",
    label: "이주·이사",
    prompt:
      "이주·이사·해외 관점에서 봐 주세요. 역마·합·충 등 이동 신호와 방위, 유리한 시기를 짚어 주세요.",
  },
  {
    hanja: "心",
    label: "마음·심리",
    prompt:
      "마음·심리·기복 관점에서 봐 주세요. 격국의 안정성, 오행 편중에서 오는 정서의 결, 스트레스 신호와 회복 자원을 짚어 주세요.",
  },
  {
    hanja: "變",
    label: "변화·전환점",
    prompt:
      "큰 변화·전환점·결단 관점에서 봐 주세요. 대운 전환, 합·충에 따른 변동 가능성, 결단의 시기를 짚어 주세요.",
  },
];

type ActiveState =
  | { kind: "loading"; category?: Category; question: string }
  | { kind: "done"; category?: Category; question: string; response: ChatResponse }
  | { kind: "error"; category?: Category; question: string; error: string };

export function ChatScreen() {
  const birth = useBirthStore((s) => s.birth);
  const chat = useChat();
  const [active, setActive] = useState<ActiveState | null>(null);
  const [input, setInput] = useState("");

  if (!birth) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center bg-bg-base">
        <Text className="text-ink-secondary">출생 정보가 없습니다.</Text>
      </SafeAreaView>
    );
  }

  const consult = (question: string, category?: Category) => {
    const q = question.trim();
    if (!q || chat.isPending) return;
    setActive({ kind: "loading", category, question: q });
    setInput("");
    chat.mutate(
      { birth, question: q },
      {
        onSuccess: (response) =>
          setActive({ kind: "done", category, question: q, response }),
        onError: (e: unknown) =>
          setActive({
            kind: "error",
            category,
            question: q,
            error: e instanceof Error ? e.message : String(e),
          }),
      },
    );
  };

  const activeHanja = active?.category?.hanja;

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView keyboardShouldPersistTaps="handled">
        <View className="gap-3 p-5">
          {/* 안내 — 처음 한 번만 가볍게 */}
          {!active && (
            <Card>
              <Text className="mb-1.5 font-serif text-base text-ink">자평 사주풀이</Text>
              <Text className="font-sans text-sm leading-6 text-ink-secondary">
                관심 영역을 누르면 그 분야 전용 사주풀이가 펼쳐집니다. 다른 영역으로 언제든
                바꿀 수 있고, 아래에 자유 질문도 입력할 수 있습니다.
              </Text>
            </Card>
          )}

          {/* 카테고리 카드 그리드 — 항상 노출, 활성 카드 골드 강조 */}
          <View className="flex-row flex-wrap gap-2">
            {CATEGORIES.map((c) => {
              const isActive = activeHanja === c.hanja;
              const isLoading = chat.isPending && isActive;
              return (
                <Pressable
                  key={c.hanja}
                  onPress={() => consult(c.prompt, c)}
                  disabled={chat.isPending}
                  className={`w-[48%] flex-row items-center justify-center gap-3 rounded-2xl border py-3.5 active:opacity-80 ${
                    isActive
                      ? "border-gold bg-bg-elevated"
                      : "border-line bg-bg-card"
                  } ${chat.isPending && !isActive ? "opacity-40" : ""}`}
                >
                  <Text
                    className={`font-serif text-2xl ${
                      isActive ? "text-gold" : "text-gold-light"
                    }`}
                  >
                    {c.hanja}
                  </Text>
                  <Text
                    className={`font-sans text-sm tracking-wider ${
                      isActive ? "text-ink" : "text-ink-secondary"
                    }`}
                  >
                    {c.label}
                  </Text>
                  {isLoading && <ActivityIndicator color="#C9A961" size="small" />}
                </Pressable>
              );
            })}
          </View>

          {/* 단일 결과 패널 — 사주풀이 */}
          {active && (
            <Card>
              {/* 헤더: 어떤 풀이인지 */}
              <View className="mb-3 flex-row items-center justify-between">
                <View className="flex-row items-baseline gap-2">
                  {active.category ? (
                    <>
                      <Text className="font-serif text-2xl text-gold-light">
                        {active.category.hanja}
                      </Text>
                      <Text className="font-serif text-base text-ink">
                        {active.category.label} 풀이
                      </Text>
                    </>
                  ) : (
                    <Text className="font-serif text-base text-ink">자유 질문 풀이</Text>
                  )}
                </View>
                {active.kind === "done" && (
                  <View
                    className={`rounded-md px-2 py-0.5 ${
                      active.response.confidence === "high"
                        ? "border border-ohaeng-mok"
                        : active.response.confidence === "low"
                          ? "border border-accent-brown"
                          : "border border-line"
                    }`}
                  >
                    <Text className="font-sans text-[10px] tracking-wider text-ink-secondary">
                      신뢰도 {active.response.confidence}
                    </Text>
                  </View>
                )}
              </View>

              {/* 로딩 */}
              {active.kind === "loading" && (
                <View className="flex-row items-center gap-2 py-2">
                  <ActivityIndicator color="#C9A961" />
                  <Text className="font-sans text-sm text-ink-secondary">
                    사주풀이를 정리하는 중…
                  </Text>
                </View>
              )}

              {/* 에러 */}
              {active.kind === "error" && (
                <View>
                  <Text className="font-sans text-sm text-ohaeng-hwa">
                    풀이를 불러오지 못했습니다.
                  </Text>
                  <Text className="mt-1 font-sans text-xs text-ink-muted">
                    {active.error}
                  </Text>
                  <View className="mt-3 w-32">
                    <Button
                      label="다시 시도"
                      onPress={() =>
                        consult(active.question, active.category)
                      }
                    />
                  </View>
                </View>
              )}

              {/* 결과 */}
              {active.kind === "done" && (
                <>
                  {/* 본문 */}
                  <Text className="font-sans text-base leading-7 text-ink">
                    {active.response.answer}
                  </Text>

                  {/* 관점 */}
                  {active.response.perspective ? (
                    <View className="mt-3 rounded-lg border border-line bg-bg-card p-3">
                      <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                        관점
                      </Text>
                      <Text className="font-sans text-sm leading-6 text-ink-secondary">
                        {active.response.perspective}
                      </Text>
                    </View>
                  ) : null}

                  {/* 시기 */}
                  {active.response.timing ? (
                    <View className="mt-2 rounded-lg border border-line bg-bg-card p-3">
                      <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                        시기
                      </Text>
                      <Text className="font-sans text-sm leading-6 text-ink-secondary">
                        {active.response.timing}
                      </Text>
                    </View>
                  ) : null}

                  {/* 주의 */}
                  {active.response.cautions.length > 0 && (
                    <View className="mt-2 rounded-lg border border-accent-brown bg-bg-card p-3">
                      <Text className="mb-1 font-sans text-[10px] tracking-widest text-accent-clay">
                        주의
                      </Text>
                      {active.response.cautions.map((c, j) => (
                        <Text
                          key={j}
                          className="font-sans text-sm leading-6 text-ink-secondary"
                        >
                          • {c}
                        </Text>
                      ))}
                    </View>
                  )}

                  {/* 학파별 견해 */}
                  {active.response.contested.length > 0 && (
                    <View className="mt-2 rounded-lg border border-line bg-bg-card p-3">
                      <Text className="mb-1 font-sans text-[10px] tracking-widest text-ink-muted">
                        학파별 견해
                      </Text>
                      {active.response.contested.map((c, j) => (
                        <Text
                          key={j}
                          className="font-sans text-sm leading-6 text-ink-secondary"
                        >
                          ◦ {c}
                        </Text>
                      ))}
                    </View>
                  )}

                  {/* 근거 */}
                  {active.response.basis ? (
                    <View className="mt-3 self-start rounded-md border border-line bg-bg-card px-2 py-1">
                      <Text className="font-serif text-xs text-gold-light">
                        근거 · {active.response.basis}
                      </Text>
                    </View>
                  ) : null}

                  {/* 인용 칩 */}
                  {active.response.citations.length > 0 && (
                    <View className="mt-2 flex-row flex-wrap gap-1.5">
                      {active.response.citations.map((c, j) => (
                        <View
                          key={j}
                          className="rounded-md border border-accent-brown bg-bg-card px-2 py-1"
                        >
                          <Text className="font-serif text-xs text-accent-clay">
                            {c.source}
                            {c.volume ? ` · ${c.volume}` : ""}
                          </Text>
                        </View>
                      ))}
                    </View>
                  )}

                  {/* 이어서 물어볼 만한 것 */}
                  {active.response.follow_up_suggestions.length > 0 && (
                    <View className="mt-3 gap-1.5">
                      <Text className="font-sans text-xs text-ink-muted">
                        이어서 물어볼 만한 것
                      </Text>
                      {active.response.follow_up_suggestions.map((s, j) => (
                        <Pressable
                          key={j}
                          onPress={() => consult(s, active.category)}
                          className="rounded-md border border-line px-3 py-2"
                        >
                          <Text className="font-sans text-sm text-ink-secondary">
                            — {s}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  )}
                </>
              )}
            </Card>
          )}
        </View>
      </ScrollView>

      {/* 자유 질문 입력 (보조) */}
      <View className="border-t border-line bg-bg-base p-3">
        <View className="flex-row gap-2">
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="자유 질문을 입력하세요 (예: 庚辰 대운 동안 유리한 분야?)"
            placeholderTextColor="#6B6357"
            multiline
            className="min-h-12 max-h-32 flex-1 rounded-2xl border border-line bg-bg-elevated px-4 py-3 font-sans text-base text-ink"
            onSubmitEditing={() => consult(input)}
          />
          <View className="w-24">
            <Button
              label="풀이"
              onPress={() => consult(input)}
              loading={chat.isPending}
            />
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

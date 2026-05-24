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

interface Turn {
  question: string;
  response: ChatResponse | null;
  error?: string;
}

interface Category {
  hanja: string;
  label: string;
  prompt: string;
}

// 12개 한자 카드 — 누르면 그 영역 전용 자문이 즉시 시작.
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

export function ChatScreen() {
  const birth = useBirthStore((s) => s.birth);
  const chat = useChat();
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);

  if (!birth) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center bg-bg-base">
        <Text className="text-ink-secondary">출생 정보가 없습니다.</Text>
      </SafeAreaView>
    );
  }

  const submit = (q: string) => {
    const question = q.trim();
    if (!question || chat.isPending) return;
    const idx = turns.length;
    setTurns((t) => [...t, { question, response: null }]);
    setInput("");
    chat.mutate(
      { birth, question },
      {
        onSuccess: (response) =>
          setTurns((t) => t.map((x, i) => (i === idx ? { ...x, response } : x))),
        onError: (e: unknown) =>
          setTurns((t) =>
            t.map((x, i) =>
              i === idx ? { ...x, error: e instanceof Error ? e.message : String(e) } : x,
            ),
          ),
      },
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView keyboardShouldPersistTaps="handled">
        <View className="gap-3 p-5">
          {/* 첫 진입 안내 (간결) */}
          {turns.length === 0 && (
            <Card>
              <Text className="mb-1.5 font-serif text-base text-ink">자평 자문</Text>
              <Text className="font-sans text-sm leading-6 text-ink-secondary">
                관심 영역을 누르면 그 분야 전용 자문이 즉시 시작됩니다. 아래 채팅으로 자유 질문도
                가능합니다. 단정은 하지 않으며, 모든 답변엔 명리 근거·고전 출처가 함께 표기됩니다.
              </Text>
            </Card>
          )}

          {/* 카테고리 카드 그리드 — 채팅 도중에도 항상 노출 (다른 영역으로 즉시 분기 가능) */}
          <View className="flex-row flex-wrap gap-2">
            {CATEGORIES.map((c) => (
              <Pressable
                key={c.hanja}
                onPress={() => submit(c.prompt)}
                disabled={chat.isPending}
                className={`w-[48%] flex-row items-center justify-center gap-3 rounded-2xl border border-line bg-bg-card py-3.5 active:opacity-80 ${
                  chat.isPending ? "opacity-50" : ""
                }`}
              >
                <Text className="font-serif text-2xl text-gold-light">{c.hanja}</Text>
                <Text className="font-sans text-sm tracking-wider text-ink-secondary">
                  {c.label}
                </Text>
              </Pressable>
            ))}
          </View>

          {turns.map((t, i) => (
            <View key={i} className="gap-2">
              {/* user */}
              <View className="self-end max-w-[85%] rounded-2xl rounded-br-md border border-line bg-bg-elevated px-4 py-3">
                <Text className="font-sans text-base text-ink">{t.question}</Text>
              </View>
              {/* ai */}
              {t.response ? (
                <Card>
                  {/* 신뢰도 배지 */}
                  <View className="mb-2 flex-row items-center justify-between">
                    <Text className="font-sans text-xs text-ink-muted">AI 자문</Text>
                    <View
                      className={`rounded-md px-2 py-0.5 ${
                        t.response.confidence === "high"
                          ? "border border-ohaeng-mok"
                          : t.response.confidence === "low"
                            ? "border border-accent-brown"
                            : "border border-line"
                      }`}
                    >
                      <Text className="font-sans text-[10px] tracking-wider text-ink-secondary">
                        신뢰도 {t.response.confidence}
                      </Text>
                    </View>
                  </View>

                  {/* 본문 */}
                  <Text className="font-sans text-base leading-7 text-ink">
                    {t.response.answer}
                  </Text>

                  {/* perspective */}
                  {t.response.perspective ? (
                    <View className="mt-3 rounded-lg border border-line bg-bg-card p-3">
                      <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                        관점
                      </Text>
                      <Text className="font-sans text-sm leading-6 text-ink-secondary">
                        {t.response.perspective}
                      </Text>
                    </View>
                  ) : null}

                  {/* timing */}
                  {t.response.timing ? (
                    <View className="mt-2 rounded-lg border border-line bg-bg-card p-3">
                      <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                        시기
                      </Text>
                      <Text className="font-sans text-sm leading-6 text-ink-secondary">
                        {t.response.timing}
                      </Text>
                    </View>
                  ) : null}

                  {/* cautions */}
                  {t.response.cautions.length > 0 && (
                    <View className="mt-2 rounded-lg border border-accent-brown bg-bg-card p-3">
                      <Text className="mb-1 font-sans text-[10px] tracking-widest text-accent-clay">
                        주의
                      </Text>
                      {t.response.cautions.map((c, j) => (
                        <Text
                          key={j}
                          className="font-sans text-sm leading-6 text-ink-secondary"
                        >
                          • {c}
                        </Text>
                      ))}
                    </View>
                  )}

                  {/* contested — 학파별 견해 차이 */}
                  {t.response.contested.length > 0 && (
                    <View className="mt-2 rounded-lg border border-line bg-bg-card p-3">
                      <Text className="mb-1 font-sans text-[10px] tracking-widest text-ink-muted">
                        학파별 견해
                      </Text>
                      {t.response.contested.map((c, j) => (
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
                  {t.response.basis ? (
                    <View className="mt-3 self-start rounded-md border border-line bg-bg-card px-2 py-1">
                      <Text className="font-serif text-xs text-gold-light">
                        근거 · {t.response.basis}
                      </Text>
                    </View>
                  ) : null}

                  {/* 인용 칩 */}
                  {t.response.citations.length > 0 && (
                    <View className="mt-2 flex-row flex-wrap gap-1.5">
                      {t.response.citations.map((c, j) => (
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

                  {t.response.follow_up_suggestions.length > 0 && (
                    <View className="mt-3 gap-1.5">
                      <Text className="font-sans text-xs text-ink-muted">이어서 물어볼 만한 것</Text>
                      {t.response.follow_up_suggestions.map((s, j) => (
                        <Pressable
                          key={j}
                          onPress={() => submit(s)}
                          className="rounded-md border border-line px-3 py-2"
                        >
                          <Text className="font-sans text-sm text-ink-secondary">— {s}</Text>
                        </Pressable>
                      ))}
                    </View>
                  )}
                </Card>
              ) : t.error ? (
                <Card>
                  <Text className="font-sans text-sm text-ohaeng-hwa">자문을 불러오지 못했습니다.</Text>
                  <Text className="mt-1 font-sans text-xs text-ink-muted">{t.error}</Text>
                </Card>
              ) : (
                <Card>
                  <View className="flex-row items-center gap-2">
                    <ActivityIndicator color="#C9A961" />
                    <Text className="font-sans text-sm text-ink-secondary">생각을 정리하는 중…</Text>
                  </View>
                </Card>
              )}
            </View>
          ))}
        </View>
      </ScrollView>

      <View className="border-t border-line bg-bg-base p-3">
        <View className="flex-row gap-2">
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="질문을 입력하세요"
            placeholderTextColor="#6B6357"
            multiline
            className="min-h-12 max-h-32 flex-1 rounded-2xl border border-line bg-bg-elevated px-4 py-3 font-sans text-base text-ink"
            onSubmitEditing={() => submit(input)}
          />
          <View className="w-28">
            <Button label="보내기" onPress={() => submit(input)} loading={chat.isPending} />
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

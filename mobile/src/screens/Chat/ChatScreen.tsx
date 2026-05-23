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

const SUGGESTIONS = ["진로", "관계", "재정 점검", "건강 흐름", "결단·실행 적기"];

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
          {turns.length === 0 && (
            <Card>
              <Text className="mb-2 font-serif text-base text-ink">AI 자문</Text>
              <Text className="font-sans text-sm leading-6 text-ink-secondary">
                중요한 결정 앞에서 사주 관점을 함께 짚어 드립니다. 단정은 하지 않으며, 모든 답변엔
                명리적 근거와 고전 출처가 함께 표기됩니다.
              </Text>
              <View className="mt-4 flex-row flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <Pressable
                    key={s}
                    onPress={() => submit(`${s}에 대한 자문을 부탁드립니다.`)}
                    className="rounded-full border border-line bg-bg-card px-3 py-1.5"
                  >
                    <Text className="font-sans text-sm text-ink-secondary">{s}</Text>
                  </Pressable>
                ))}
              </View>
            </Card>
          )}

          {turns.map((t, i) => (
            <View key={i} className="gap-2">
              {/* user */}
              <View className="self-end max-w-[85%] rounded-2xl rounded-br-md border border-line bg-bg-elevated px-4 py-3">
                <Text className="font-sans text-base text-ink">{t.question}</Text>
              </View>
              {/* ai */}
              {t.response ? (
                <Card>
                  <Text className="font-sans text-base leading-7 text-ink">
                    {t.response.answer}
                  </Text>
                  {t.response.basis ? (
                    <View className="mt-3 self-start rounded-md border border-line bg-bg-card px-2 py-1">
                      <Text className="font-serif text-xs text-gold-light">
                        근거 · {t.response.basis}
                      </Text>
                    </View>
                  ) : null}
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

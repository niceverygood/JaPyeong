/**
 * 결정 도우미(決) 화면 — 사주 + 두 선택지 A/B + 컨텍스트 → LLM 비교 자문.
 *
 * 양쪽 옵션 textarea, 옵션 컨텍스트, lean 시각화 (A/B/balanced 토글 표시).
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useDecision } from "@/api/decision";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { HanjaText } from "@/components/primitives/HanjaText";
import type { RootStackParamList } from "@/navigation/types";
import { useBirthStore } from "@/stores/birthStore";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "Decision">;

function MultiField({
  label,
  value,
  onChangeText,
  placeholder,
  minHeight = 80,
}: {
  label: string;
  value: string;
  onChangeText: (v: string) => void;
  placeholder?: string;
  minHeight?: number;
}) {
  return (
    <View className="mb-4">
      <Text className="mb-2 font-sans text-sm text-ink-secondary">{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.text.faint}
        multiline
        textAlignVertical="top"
        style={{ minHeight }}
        className="rounded-lg border border-line bg-bg-card px-4 py-3 font-sans text-base text-ink"
      />
    </View>
  );
}

function LeanBadge({ lean }: { lean: "A" | "B" | "balanced" }) {
  const map = {
    A: { label: "A 쪽으로 살짝 기움", color: colors.gold.primary },
    B: { label: "B 쪽으로 살짝 기움", color: colors.gold.primary },
    balanced: { label: "균형 (확정 안 됨)", color: colors.text.secondary },
  } as const;
  const { label, color } = map[lean];
  return (
    <View
      className="self-start rounded-md border px-2.5 py-1"
      style={{ borderColor: color }}
    >
      <Text className="font-sans text-xs" style={{ color }}>
        {label}
      </Text>
    </View>
  );
}

export function DecisionScreen() {
  const birth = useBirthStore((s) => s.birth);
  const navigation = useNavigation<Nav>();
  const mutation = useDecision();

  const [aTitle, setATitle] = useState("");
  const [aDesc, setADesc] = useState("");
  const [bTitle, setBTitle] = useState("");
  const [bDesc, setBDesc] = useState("");
  const [context, setContext] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!birth) {
    return (
      <SafeAreaView className="flex-1 bg-bg-base p-6">
        <Text className="mb-4 font-serif text-2xl text-ink">결정 도우미 (決)</Text>
        <Text className="mb-4 font-sans text-sm text-ink-secondary">
          두 선택지를 사주 관점에서 비교하려면 먼저 본인의 명식이 필요합니다.
        </Text>
        <Button
          label="명식 입력하기"
          onPress={() => navigation.navigate("Onboarding")}
        />
      </SafeAreaView>
    );
  }

  const submit = () => {
    if (!aTitle.trim() || !aDesc.trim() || !bTitle.trim() || !bDesc.trim()) {
      setError("두 선택지의 제목과 설명을 모두 입력해 주세요.");
      return;
    }
    setError(null);
    mutation.mutate({
      birth,
      option_a: { title: aTitle.trim(), description: aDesc.trim() },
      option_b: { title: bTitle.trim(), description: bDesc.trim() },
      context: context.trim() || null,
    });
  };

  const res = mutation.data;

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView keyboardShouldPersistTaps="handled">
        <View className="p-5 pb-10">
          <View className="mb-4">
            <Text className="font-serif text-3xl text-ink">
              決 <Text className="text-gold">결정 도우미</Text>
            </Text>
            <Text className="mt-1 font-sans text-sm text-ink-secondary">
              두 선택지를 사주의 결을 거울 삼아 비춰 봅니다. 최종 결정은 본인이 합니다.
            </Text>
          </View>

          {/* 옵션 A */}
          <Card className="mb-3">
            <Text className="mb-3 font-serif text-base text-gold-light">
              選 옵션 A
            </Text>
            <MultiField
              label="제목 (1줄)"
              value={aTitle}
              onChangeText={setATitle}
              placeholder="예: 이직 (A회사 SaaS 백엔드)"
              minHeight={44}
            />
            <MultiField
              label="설명 (왜 이 선택을 고려하는지)"
              value={aDesc}
              onChangeText={setADesc}
              placeholder="예: 연봉 +20%, 새로운 도메인이지만 출장 잦음. 의사결정 권한 큼."
              minHeight={90}
            />
          </Card>

          {/* 옵션 B */}
          <Card className="mb-3">
            <Text className="mb-3 font-serif text-base text-gold-light">
              選 옵션 B
            </Text>
            <MultiField
              label="제목 (1줄)"
              value={bTitle}
              onChangeText={setBTitle}
              placeholder="예: 잔류 (현 회사 시니어 트랙)"
              minHeight={44}
            />
            <MultiField
              label="설명"
              value={bDesc}
              onChangeText={setBDesc}
              placeholder="예: 안정·인맥 자산. 6개월 후 승진 기회. 성장 정체 우려."
              minHeight={90}
            />
          </Card>

          {/* 컨텍스트 */}
          <MultiField
            label="추가 맥락 (선택)"
            value={context}
            onChangeText={setContext}
            placeholder="예: 올해 4월에 제안 받음. 가족 부양 부담 큼."
            minHeight={70}
          />

          {error && (
            <Text className="mb-3 font-sans text-sm text-ohaeng-hwa">{error}</Text>
          )}

          <Button
            label={mutation.isPending ? "비교 중…" : "사주로 비교하기"}
            onPress={submit}
            disabled={mutation.isPending}
          />

          {mutation.isPending && (
            <View className="mt-4 flex-row items-center justify-center gap-2">
              <ActivityIndicator color={colors.gold.primary} />
              <Text className="font-sans text-sm text-ink-secondary">
                두 선택지를 사주의 결로 비춰 보는 중…
              </Text>
            </View>
          )}

          {mutation.isError && (
            <View className="mt-4 rounded-lg border border-accent-brown bg-bg-card p-3">
              <Text className="font-sans text-sm text-ohaeng-hwa">
                자문을 불러오지 못했습니다.
              </Text>
              <Text className="mt-1 font-sans text-xs text-ink-muted">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : String(mutation.error)}
              </Text>
            </View>
          )}

          {res && (
            <Card className="mt-4">
              {/* lean 배지 + confidence */}
              <View className="mb-3 flex-row items-baseline justify-between">
                <LeanBadge lean={res.lean} />
                <View
                  className={`rounded-md border px-2 py-0.5 ${
                    res.confidence === "high"
                      ? "border-ohaeng-mok"
                      : res.confidence === "low"
                        ? "border-accent-brown"
                        : "border-line"
                  }`}
                >
                  <Text className="font-sans text-[10px] tracking-wider text-ink-secondary">
                    신뢰도 {res.confidence}
                  </Text>
                </View>
              </View>

              {/* lean 이유 */}
              {res.lean_reason ? (
                <HanjaText className="mb-3 font-sans text-sm leading-6 text-ink-secondary">
                  {res.lean_reason}
                </HanjaText>
              ) : null}

              {/* 두 옵션 나란히 */}
              <View className="mb-3 gap-2">
                <View className="rounded-lg border border-line bg-bg-card p-3">
                  <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                    옵션 A 관점
                  </Text>
                  <Text className="mb-1 font-serif text-sm text-ink">{aTitle}</Text>
                  <HanjaText className="font-sans text-sm leading-6 text-ink-secondary">
                    {res.option_a_view}
                  </HanjaText>
                </View>
                <View className="rounded-lg border border-line bg-bg-card p-3">
                  <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                    옵션 B 관점
                  </Text>
                  <Text className="mb-1 font-serif text-sm text-ink">{bTitle}</Text>
                  <HanjaText className="font-sans text-sm leading-6 text-ink-secondary">
                    {res.option_b_view}
                  </HanjaText>
                </View>
              </View>

              {/* 비교 */}
              {res.comparison ? (
                <View className="mb-3 rounded-lg border border-line bg-bg-card p-3">
                  <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                    A·B 비교
                  </Text>
                  <HanjaText className="font-sans text-sm leading-6 text-ink-secondary">
                    {res.comparison}
                  </HanjaText>
                </View>
              ) : null}

              {/* 종합 자문 */}
              {res.answer ? (
                <View className="mb-3 rounded-lg border border-gold bg-bg-elevated p-3">
                  <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold">
                    종합 자문
                  </Text>
                  <HanjaText className="font-sans text-base leading-7 text-ink">
                    {res.answer}
                  </HanjaText>
                </View>
              ) : null}

              {/* 부가 (관점·시기·주의·학파·근거·인용) */}
              {res.perspective ? (
                <View className="mt-2 rounded-lg border border-line bg-bg-card p-3">
                  <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                    관점
                  </Text>
                  <HanjaText className="font-sans text-sm leading-6 text-ink-secondary">
                    {res.perspective}
                  </HanjaText>
                </View>
              ) : null}

              {res.timing ? (
                <View className="mt-2 rounded-lg border border-line bg-bg-card p-3">
                  <Text className="mb-1 font-sans text-[10px] tracking-widest text-gold-light">
                    시기
                  </Text>
                  <HanjaText className="font-sans text-sm leading-6 text-ink-secondary">
                    {res.timing}
                  </HanjaText>
                </View>
              ) : null}

              {res.cautions.length > 0 && (
                <View className="mt-2 rounded-lg border border-accent-brown bg-bg-card p-3">
                  <Text className="mb-1 font-sans text-[10px] tracking-widest text-accent-clay">
                    주의
                  </Text>
                  {res.cautions.map((c, j) => (
                    <HanjaText
                      key={j}
                      className="font-sans text-sm leading-6 text-ink-secondary"
                    >
                      {`• ${c}`}
                    </HanjaText>
                  ))}
                </View>
              )}

              {res.contested.length > 0 && (
                <View className="mt-2 rounded-lg border border-line bg-bg-card p-3">
                  <Text className="mb-1 font-sans text-[10px] tracking-widest text-ink-muted">
                    학파별 견해
                  </Text>
                  {res.contested.map((c, j) => (
                    <HanjaText
                      key={j}
                      className="font-sans text-sm leading-6 text-ink-secondary"
                    >
                      {`◦ ${c}`}
                    </HanjaText>
                  ))}
                </View>
              )}

              {res.basis ? (
                <View className="mt-3 self-start rounded-md border border-line bg-bg-card px-2 py-1">
                  <HanjaText className="font-serif text-xs text-gold-light">
                    {`근거 · ${res.basis}`}
                  </HanjaText>
                </View>
              ) : null}

              {res.citations.length > 0 && (
                <View className="mt-2 flex-row flex-wrap gap-1.5">
                  {res.citations.map((c, j) => (
                    <View
                      key={j}
                      className="rounded-md border border-accent-brown bg-bg-card px-2 py-1"
                    >
                      <HanjaText className="font-serif text-xs text-accent-clay">
                        {c.source + (c.volume ? ` · ${c.volume}` : "")}
                      </HanjaText>
                    </View>
                  ))}
                </View>
              )}

              <Text className="mt-4 text-center font-sans text-[10px] text-ink-muted">
                자평은 결정의 참고일 뿐, 최종 결정은 본인이 합니다.
              </Text>
            </Card>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

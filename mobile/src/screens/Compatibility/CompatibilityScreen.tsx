/**
 * 궁합(宮合) 화면 — 두 사주 비교 + LLM 자문.
 *
 * UX:
 *  1. 내 사주는 birthStore에서 자동 사용(있을 때) / 없으면 입력 폼
 *  2. 상대 사주는 항상 입력 폼
 *  3. 관계 유형 선택 (연애/결혼/동업/가족)
 *  4. "궁합 보기" → 결과 카드 (요약 카드 + 자문 본문 + 학파 견해)
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

import {
  useCompatibility,
  type CompatResponse,
  type RelationshipType,
} from "@/api/compatibility";
import type { BirthInput, Calendar, Gender } from "@/api/types";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Field } from "@/components/primitives/Field";
import { HanjaText } from "@/components/primitives/HanjaText";
import type { RootStackParamList } from "@/navigation/types";
import { useBirthStore } from "@/stores/birthStore";
import { colors } from "@/theme";

const SEOUL = { longitude: 126.9784, latitude: 37.5665, timezone: "Asia/Seoul" };

type Nav = NativeStackNavigationProp<RootStackParamList, "Compatibility">;

const REL_OPTIONS: { value: RelationshipType; label: string; hanja: string }[] = [
  { value: "romantic", label: "연애", hanja: "緣" },
  { value: "marriage", label: "결혼", hanja: "婚" },
  { value: "business", label: "동업", hanja: "業" },
  { value: "family", label: "가족", hanja: "家" },
];

function Segmented<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <View className="mb-3 flex-row gap-2">
      {options.map((o) => {
        const active = o.value === value;
        return (
          <Pressable
            key={o.value}
            onPress={() => onChange(o.value)}
            className="h-11 flex-1 items-center justify-center rounded-lg border"
            style={{
              backgroundColor: active ? "rgba(201,169,97,0.10)" : colors.bg.card,
              borderColor: active ? colors.gold.primary : colors.line,
            }}
          >
            <Text className={`font-sans text-sm ${active ? "text-gold" : "text-ink-secondary"}`}>
              {o.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

/** 한 사람의 입력 폼 */
function PersonForm({
  title,
  hanja,
  state,
  setState,
}: {
  title: string;
  hanja: string;
  state: PersonState;
  setState: (s: PersonState) => void;
}) {
  const update = (patch: Partial<PersonState>) => setState({ ...state, ...patch });

  return (
    <Card className="mb-3">
      <View className="mb-3 flex-row items-baseline gap-2">
        <Text className="font-serif text-2xl text-gold-light">{hanja}</Text>
        <Text className="font-serif text-base text-ink">{title}</Text>
      </View>

      <Field
        label="이름 (선택)"
        value={state.label}
        onChangeText={(v) => update({ label: v })}
        placeholder="호칭"
      />

      <Text className="mb-2 font-sans text-sm text-ink-secondary">성별</Text>
      <Segmented
        value={state.gender}
        onChange={(v) => update({ gender: v as Gender })}
        options={[
          { value: "M", label: "남성" },
          { value: "F", label: "여성" },
        ]}
      />

      <Text className="mb-2 font-sans text-sm text-ink-secondary">달력</Text>
      <Segmented
        value={state.calendar}
        onChange={(v) => update({ calendar: v as Calendar })}
        options={[
          { value: "solar", label: "양력" },
          { value: "lunar", label: "음력" },
        ]}
      />

      <View className="flex-row gap-2">
        <View className="flex-1">
          <Field
            label="년"
            value={state.year}
            onChangeText={(v) => update({ year: v })}
            placeholder="1990"
            keyboardType="number-pad"
          />
        </View>
        <View className="flex-1">
          <Field
            label="월"
            value={state.month}
            onChangeText={(v) => update({ month: v })}
            placeholder="5"
            keyboardType="number-pad"
          />
        </View>
        <View className="flex-1">
          <Field
            label="일"
            value={state.day}
            onChangeText={(v) => update({ day: v })}
            placeholder="20"
            keyboardType="number-pad"
          />
        </View>
      </View>

      <View className="flex-row gap-2">
        <View className="flex-1">
          <Field
            label="시 (선택)"
            value={state.hour}
            onChangeText={(v) => update({ hour: v })}
            placeholder="14"
            keyboardType="number-pad"
          />
        </View>
        <View className="flex-1">
          <Field
            label="분 (선택)"
            value={state.minute}
            onChangeText={(v) => update({ minute: v })}
            placeholder="30"
            keyboardType="number-pad"
          />
        </View>
      </View>
    </Card>
  );
}

interface PersonState {
  label: string;
  gender: Gender;
  calendar: Calendar;
  year: string;
  month: string;
  day: string;
  hour: string;
  minute: string;
}

const EMPTY: PersonState = {
  label: "",
  gender: "M",
  calendar: "solar",
  year: "",
  month: "",
  day: "",
  hour: "",
  minute: "",
};

function birthFromBirthInput(b: BirthInput): PersonState {
  return {
    label: b.name ?? "",
    gender: b.gender,
    calendar: b.calendar,
    year: String(b.year),
    month: String(b.month),
    day: String(b.day),
    hour: b.hour != null ? String(b.hour) : "",
    minute: b.minute != null ? String(b.minute) : "",
  };
}

function toBirthInput(s: PersonState): BirthInput | string {
  const y = Number(s.year);
  const m = Number(s.month);
  const d = Number(s.day);
  if (!y || !m || !d || m < 1 || m > 12 || d < 1 || d > 31) {
    return "생년월일을 정확히 입력해 주세요.";
  }
  const hasHour = s.hour.trim() !== "";
  return {
    name: s.label || undefined,
    gender: s.gender,
    calendar: s.calendar,
    year: y,
    month: m,
    day: d,
    hour: hasHour ? Number(s.hour) : null,
    minute: hasHour ? Number(s.minute || "0") : null,
    ...SEOUL,
  };
}

function ResultPanel({ res }: { res: CompatResponse }) {
  const a = res.analysis;
  const gain = a.element_combined.balance_gain;
  const gainColor =
    gain > 0.05
      ? "text-ohaeng-mok"
      : gain < -0.05
        ? "text-ohaeng-hwa"
        : "text-ink-secondary";

  return (
    <Card className="mt-3">
      {/* 요약 카드 */}
      <View className="mb-3 flex-row items-baseline justify-between">
        <Text className="font-serif text-base text-ink">궁합 풀이</Text>
        <View
          className={`rounded-md px-2 py-0.5 border ${
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

      {/* 결정론 요약 */}
      <View className="mb-3 flex-row gap-2">
        <View className="flex-1 rounded-lg border border-line bg-bg-card p-3">
          <Text className="font-sans text-[10px] tracking-widest text-gold-light">
            일간 관계
          </Text>
          <HanjaText className="mt-1 font-serif text-sm text-ink">
            {`${a.day_master_pair.day_master_a} ↔ ${a.day_master_pair.day_master_b}`}
          </HanjaText>
          <Text className="mt-0.5 font-sans text-xs text-ink-secondary">
            {a.day_master_pair.dynamic}
          </Text>
        </View>
        <View className="flex-1 rounded-lg border border-line bg-bg-card p-3">
          <Text className="font-sans text-[10px] tracking-widest text-gold-light">
            합 / 충
          </Text>
          <Text className="mt-1 font-serif text-sm text-ink">
            합 {a.strong_bonds_count} · 충/형/해/파 {a.conflicts_count}
          </Text>
          <Text className={`mt-0.5 font-sans text-xs ${gainColor}`}>
            오행 보완 {gain >= 0 ? "+" : ""}{gain.toFixed(2)}
          </Text>
        </View>
      </View>

      {res.flags.length > 0 && res.flags.includes("crisis") ? null : (
        <>
          {/* 본문 */}
          <HanjaText className="font-sans text-base leading-7 text-ink">
            {res.answer}
          </HanjaText>

          {res.perspective ? (
            <View className="mt-3 rounded-lg border border-line bg-bg-card p-3">
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

          {/* 결정론 노트 (디버그성, 작게) */}
          {a.notes.length > 0 && (
            <View className="mt-4 rounded-md bg-bg-card p-2.5">
              <Text className="mb-1 font-sans text-[10px] tracking-widest text-ink-muted">
                엔진 신호
              </Text>
              {a.notes.map((n, j) => (
                <HanjaText
                  key={j}
                  className="font-sans text-xs leading-5 text-ink-muted"
                >
                  {`· ${n}`}
                </HanjaText>
              ))}
            </View>
          )}
        </>
      )}
    </Card>
  );
}

export function CompatibilityScreen() {
  const navigation = useNavigation<Nav>();
  const myBirth = useBirthStore((s) => s.birth);

  const [aState, setAState] = useState<PersonState>(
    myBirth ? birthFromBirthInput(myBirth) : { ...EMPTY, label: "나" },
  );
  const [bState, setBState] = useState<PersonState>({ ...EMPTY, label: "상대" });
  const [relType, setRelType] = useState<RelationshipType>("romantic");
  const [error, setError] = useState<string | null>(null);

  const mutation = useCompatibility();

  const submit = () => {
    const ba = toBirthInput(aState);
    const bb = toBirthInput(bState);
    if (typeof ba === "string") {
      setError(`내 사주: ${ba}`);
      return;
    }
    if (typeof bb === "string") {
      setError(`상대 사주: ${bb}`);
      return;
    }
    setError(null);
    mutation.mutate({
      birth_a: ba,
      birth_b: bb,
      relationship_type: relType,
      label_a: aState.label || null,
      label_b: bState.label || null,
    });
  };

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView keyboardShouldPersistTaps="handled">
        <View className="p-5 pb-10">
          {/* 헤더 */}
          <View className="mb-4">
            <Text className="font-serif text-3xl text-ink">
              宮合 <Text className="text-gold">궁합</Text>
            </Text>
            <Text className="mt-1 font-sans text-sm text-ink-secondary">
              두 사주의 결을 비교해 관계의 흐름을 짚어 드립니다.
            </Text>
          </View>

          {/* 관계 유형 선택 */}
          <View className="mb-2">
            <Text className="mb-2 font-sans text-sm text-ink-secondary">관계 유형</Text>
            <View className="flex-row gap-2">
              {REL_OPTIONS.map((o) => {
                const active = relType === o.value;
                return (
                  <Pressable
                    key={o.value}
                    onPress={() => setRelType(o.value)}
                    className="h-14 flex-1 flex-row items-center justify-center gap-2 rounded-lg border"
                    style={{
                      backgroundColor: active ? "rgba(201,169,97,0.10)" : colors.bg.card,
                      borderColor: active ? colors.gold.primary : colors.line,
                    }}
                  >
                    <Text
                      className={`font-serif text-xl ${active ? "text-gold" : "text-gold-light"}`}
                    >
                      {o.hanja}
                    </Text>
                    <Text
                      className={`font-sans text-sm ${
                        active ? "text-ink" : "text-ink-secondary"
                      }`}
                    >
                      {o.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>

          {/* 두 사람 입력 폼 */}
          <View className="mt-4">
            <PersonForm
              title={myBirth ? "내 사주" : "사람 1"}
              hanja="我"
              state={aState}
              setState={setAState}
            />
            <PersonForm title="상대 사주" hanja="彼" state={bState} setState={setBState} />
          </View>

          {error && (
            <Text className="mb-3 font-sans text-sm text-ohaeng-hwa">{error}</Text>
          )}

          <Button
            label={mutation.isPending ? "분석 중…" : "궁합 보기"}
            onPress={submit}
            disabled={mutation.isPending}
          />

          {mutation.isPending && (
            <View className="mt-4 flex-row items-center justify-center gap-2">
              <ActivityIndicator color="#C9A961" />
              <Text className="font-sans text-sm text-ink-secondary">
                두 사주를 비교하는 중…
              </Text>
            </View>
          )}

          {mutation.isError && !mutation.isPending && (
            <View className="mt-4 rounded-lg border border-accent-brown bg-bg-card p-3">
              <Text className="font-sans text-sm text-ohaeng-hwa">
                궁합 자문을 불러오지 못했습니다.
              </Text>
              <Text className="mt-1 font-sans text-xs text-ink-muted">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : String(mutation.error)}
              </Text>
            </View>
          )}

          {mutation.data && <ResultPanel res={mutation.data} />}

          {/* 명식 입력으로 돌아가기 */}
          {!myBirth && (
            <Pressable
              onPress={() => navigation.navigate("Onboarding")}
              className="mt-4 self-center"
            >
              <Text className="font-sans text-xs text-ink-muted underline">
                내 명식을 먼저 입력하시려면
              </Text>
            </Pressable>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

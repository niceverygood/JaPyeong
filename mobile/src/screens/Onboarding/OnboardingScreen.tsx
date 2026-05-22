import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import type { BirthInput, Calendar, Gender } from "@/api/types";
import { Button } from "@/components/primitives/Button";
import { Field } from "@/components/primitives/Field";
import { useBirthStore } from "@/stores/birthStore";
import type { RootStackParamList } from "@/navigation/types";

// 서울 기본 좌표 (진태양시 보정용)
const SEOUL = { longitude: 126.9784, latitude: 37.5665, timezone: "Asia/Seoul" };

type Nav = NativeStackNavigationProp<RootStackParamList, "Onboarding">;

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
    <View className="mb-4 flex-row gap-2">
      {options.map((o) => {
        const active = o.value === value;
        return (
          <Pressable
            key={o.value}
            onPress={() => onChange(o.value)}
            className={`h-12 flex-1 items-center justify-center rounded-xl border ${
              active ? "border-gold bg-gold/10" : "border-line bg-bg-elevated"
            }`}
          >
            <Text className={`font-sans ${active ? "text-gold" : "text-ink-secondary"}`}>
              {o.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function OnboardingScreen() {
  const navigation = useNavigation<Nav>();
  const setBirth = useBirthStore((s) => s.setBirth);

  const [name, setName] = useState("");
  const [gender, setGender] = useState<Gender>("M");
  const [calendar, setCalendar] = useState<Calendar>("solar");
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const [day, setDay] = useState("");
  const [hour, setHour] = useState("");
  const [minute, setMinute] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    const y = Number(year);
    const m = Number(month);
    const d = Number(day);
    if (!y || !m || !d || m < 1 || m > 12 || d < 1 || d > 31) {
      setError("생년월일을 정확히 입력해 주세요.");
      return;
    }
    const hasHour = hour.trim() !== "";
    const birth: BirthInput = {
      name: name || undefined,
      gender,
      calendar,
      year: y,
      month: m,
      day: d,
      hour: hasHour ? Number(hour) : null,
      minute: hasHour ? Number(minute || "0") : null,
      ...SEOUL,
    };
    setBirth(birth);
    setError(null);
    navigation.navigate("Saju");
  };

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <ScrollView keyboardShouldPersistTaps="handled">
        <View className="p-5">
        <Text className="mb-1 font-serif text-3xl text-gold">子平</Text>
        <Text className="mb-6 font-sans text-base text-ink-secondary">
          출생 정보를 입력하면 사주 원국을 분석합니다.
        </Text>

        <Field label="이름 (선택)" value={name} onChangeText={setName} placeholder="실명 또는 호칭" />

        <Text className="mb-2 font-sans text-sm text-ink-secondary">성별</Text>
        <Segmented
          value={gender}
          onChange={setGender}
          options={[
            { value: "M", label: "남성" },
            { value: "F", label: "여성" },
          ]}
        />

        <Text className="mb-2 font-sans text-sm text-ink-secondary">달력</Text>
        <Segmented
          value={calendar}
          onChange={setCalendar}
          options={[
            { value: "solar", label: "양력" },
            { value: "lunar", label: "음력" },
          ]}
        />

        <View className="flex-row gap-3">
          <View className="flex-1">
            <Field label="년" value={year} onChangeText={setYear} placeholder="1985" keyboardType="number-pad" />
          </View>
          <View className="flex-1">
            <Field label="월" value={month} onChangeText={setMonth} placeholder="6" keyboardType="number-pad" />
          </View>
          <View className="flex-1">
            <Field label="일" value={day} onChangeText={setDay} placeholder="23" keyboardType="number-pad" />
          </View>
        </View>

        <View className="flex-row gap-3">
          <View className="flex-1">
            <Field label="시 (선택)" value={hour} onChangeText={setHour} placeholder="14" keyboardType="number-pad" />
          </View>
          <View className="flex-1">
            <Field label="분 (선택)" value={minute} onChangeText={setMinute} placeholder="30" keyboardType="number-pad" />
          </View>
        </View>

        {error && <Text className="mb-3 font-sans text-sm text-ohaeng-hwa">{error}</Text>}

        <View className="mt-2">
          <Button label="원국 분석하기" onPress={submit} />
        </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

import { Text, View } from "react-native";

import type { FourPillars, Pillar } from "@/api/types";
import { colors } from "@/theme";

const COLUMNS: { key: keyof FourPillars; label: string; ko: string }[] = [
  { key: "year", label: "年", ko: "년주" },
  { key: "month", label: "月", ko: "월주" },
  { key: "day", label: "日", ko: "일주" },
  { key: "hour", label: "時", ko: "시주" },
];

const GAN_ELEMENT: Record<string, keyof typeof colors.ohaeng> = {
  甲: "mok",
  乙: "mok",
  丙: "hwa",
  丁: "hwa",
  戊: "to",
  己: "to",
  庚: "geum",
  辛: "geum",
  壬: "su",
  癸: "su",
};

const JI_ELEMENT: Record<string, keyof typeof colors.ohaeng> = {
  寅: "mok",
  卯: "mok",
  巳: "hwa",
  午: "hwa",
  辰: "to",
  戌: "to",
  丑: "to",
  未: "to",
  申: "geum",
  酉: "geum",
  子: "su",
  亥: "su",
};

function elementColor(char: string | undefined, source: "gan" | "ji") {
  if (!char) return colors.text.faint;
  const key = source === "gan" ? GAN_ELEMENT[char] : JI_ELEMENT[char];
  return key ? colors.ohaeng[key] : colors.text.primary;
}

function PillarCell({
  pillar,
  label,
  ko,
  isDay,
}: {
  pillar: Pillar | null;
  label: string;
  ko: string;
  isDay: boolean;
}) {
  return (
    <View
      className="flex-1 rounded-lg border p-2"
      style={{
        backgroundColor: isDay ? "rgba(201,169,97,0.07)" : colors.bg.elevated,
        borderColor: isDay ? "rgba(201,169,97,0.45)" : colors.line,
      }}
    >
      <Text className="mb-1 text-center font-sans text-[10px] text-ink-muted">{ko}</Text>
      <Text className="mb-2 text-center font-serif text-xs text-ink-muted">{label}</Text>
      <View className="mb-2 h-14 items-center justify-center rounded-md border border-line bg-bg-card">
        <Text className="font-serif text-3xl" style={{ color: elementColor(pillar?.gan, "gan") }}>
          {pillar ? pillar.gan : "-"}
        </Text>
      </View>
      <View className="h-14 items-center justify-center rounded-md border border-line bg-bg-card">
        <Text className="font-serif text-3xl" style={{ color: elementColor(pillar?.ji, "ji") }}>
          {pillar ? pillar.ji : "-"}
        </Text>
      </View>
    </View>
  );
}

export function SajuGrid({ pillars }: { pillars: FourPillars }) {
  return (
    <View className="flex-row gap-2">
      {COLUMNS.map((c) => (
        <PillarCell
          key={c.key}
          label={c.label}
          ko={c.ko}
          pillar={pillars[c.key]}
          isDay={c.key === "day"}
        />
      ))}
    </View>
  );
}

export function MiniSajuStrip({ pillars }: { pillars: FourPillars }) {
  return (
    <View className="flex-row gap-1">
      {COLUMNS.map((c) => {
        const pillar = pillars[c.key];
        const isDay = c.key === "day";
        return (
          <View
            key={c.key}
            className="flex-1 rounded-md border px-1 py-2"
            style={{
              backgroundColor: isDay ? "rgba(201,169,97,0.10)" : colors.bg.card,
              borderColor: isDay ? "rgba(201,169,97,0.45)" : colors.line,
            }}
          >
            <View className="flex-row items-baseline justify-center gap-1">
              <Text
                className="font-serif text-lg"
                style={{ color: elementColor(pillar?.gan, "gan") }}
              >
                {pillar ? pillar.gan : "-"}
              </Text>
              <Text
                className="font-serif text-lg"
                style={{ color: elementColor(pillar?.ji, "ji") }}
              >
                {pillar ? pillar.ji : "-"}
              </Text>
            </View>
            <Text className="mt-0.5 text-center font-sans text-[9px] text-ink-muted">
              {c.ko}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

import { Text, View } from "react-native";

import type { FourPillars, Pillar } from "@/api/types";

const COLUMNS: { key: keyof FourPillars; label: string }[] = [
  { key: "year", label: "年" },
  { key: "month", label: "月" },
  { key: "day", label: "日" },
  { key: "hour", label: "時" },
];

function PillarCell({ pillar, label }: { pillar: Pillar | null; label: string }) {
  return (
    <View className="flex-1 items-center">
      <Text className="mb-2 font-sans text-xs text-ink-muted">{label}</Text>
      <View className="mb-2 h-16 w-16 items-center justify-center rounded-xl border border-line bg-bg-card">
        <Text className="font-serif text-3xl text-gold-light">
          {pillar ? pillar.gan : "—"}
        </Text>
      </View>
      <View className="h-16 w-16 items-center justify-center rounded-xl border border-line bg-bg-card">
        <Text className="font-serif text-3xl text-ink">
          {pillar ? pillar.ji : "—"}
        </Text>
      </View>
    </View>
  );
}

export function SajuGrid({ pillars }: { pillars: FourPillars }) {
  return (
    <View className="flex-row justify-between gap-2">
      {COLUMNS.map((c) => (
        <PillarCell key={c.key} label={c.label} pillar={pillars[c.key]} />
      ))}
    </View>
  );
}

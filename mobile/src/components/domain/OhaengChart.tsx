import { Text, View } from "react-native";

import type { FiveElements } from "@/api/types";
import { colors } from "@/theme";

const ROWS: { key: keyof FiveElements; label: string; color: string }[] = [
  { key: "mok", label: "木 목", color: colors.ohaeng.mok },
  { key: "hwa", label: "火 화", color: colors.ohaeng.hwa },
  { key: "to", label: "土 토", color: colors.ohaeng.to },
  { key: "geum", label: "金 금", color: colors.ohaeng.geum },
  { key: "su", label: "水 수", color: colors.ohaeng.su },
];

export function OhaengChart({ five }: { five: FiveElements }) {
  const max = Math.max(five.mok, five.hwa, five.to, five.geum, five.su, 1);
  return (
    <View>
      {ROWS.map((r) => {
        const value = five[r.key] as number;
        const pct = Math.round((value / max) * 100);
        return (
          <View key={r.key} className="mb-3 flex-row items-center">
            <Text className="w-14 font-serif text-sm text-ink">{r.label}</Text>
            <View className="mx-2 h-3 flex-1 overflow-hidden rounded-full bg-bg-card">
              <View
                style={{ width: `${pct}%`, backgroundColor: r.color }}
                className="h-full rounded-full"
              />
            </View>
            <Text className="w-10 text-right font-sans text-xs text-ink-secondary">
              {value.toFixed(1)}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

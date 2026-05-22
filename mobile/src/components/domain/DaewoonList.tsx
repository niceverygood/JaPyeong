import { ScrollView, Text, View } from "react-native";

import type { Daewoon } from "@/api/types";

export function DaewoonList({ daewoon }: { daewoon: Daewoon }) {
  const dirLabel = daewoon.direction === "forward" ? "순행" : "역행";
  return (
    <View>
      <Text className="mb-3 font-sans text-sm text-ink-secondary">
        {dirLabel} · 대운수 {daewoon.start_age}
      </Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View className="flex-row gap-2">
          {daewoon.periods.map((p) => (
            <View
              key={p.sequence}
              className="w-16 items-center rounded-xl border border-line bg-bg-card py-3"
            >
              <Text className="mb-1 font-sans text-xs text-ink-muted">
                {p.start_age}세
              </Text>
              <Text className="font-serif text-xl text-gold-light">{p.gan}</Text>
              <Text className="font-serif text-xl text-ink">{p.ji}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

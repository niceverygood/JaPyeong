import { ScrollView, Text, View } from "react-native";

import type { Daewoon } from "@/api/types";

export function DaewoonList({ daewoon }: { daewoon: Daewoon }) {
  const dirLabel = daewoon.direction === "forward" ? "순행" : "역행";
  return (
    <View>
      <View className="mb-3 self-start rounded-md border border-line bg-bg-card px-2.5 py-1">
        <Text className="font-sans text-xs text-ink-secondary">
          {dirLabel} · {daewoon.start_age}세 시작
        </Text>
      </View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View className="flex-row gap-2">
          {daewoon.periods.map((p) => (
            <View
              key={p.sequence}
              className="w-16 items-center rounded-lg border border-line bg-bg-card py-3"
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

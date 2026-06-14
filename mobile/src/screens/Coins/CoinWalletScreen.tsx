/**
 * 내 코인 — 선충전 지갑 (ARPU).
 *
 * 잔액 + 충전팩(소비성 IAP) + 단건 상품 안내 + 거래 내역.
 * 네이티브에서만 충전 가능(스토어 결제). 웹은 안내만.
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ActivityIndicator, Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  getCoinBalance,
  getCoinLedger,
  getCoinProducts,
  type ChargePack,
} from "@/api/coins";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useCoinCharge } from "@/hooks/useCoinCharge";
import type { CoinPackCode } from "@/lib/iap";
import type { RootStackParamList } from "@/navigation/types";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "Coins">;

const KIND_KO: Record<string, string> = {
  charge: "충전",
  bonus: "보너스",
  spend: "사용",
  refund: "환원",
  expire: "소멸",
  adjust: "조정",
};

function won(n: number): string {
  return n.toLocaleString("ko-KR");
}

export function CoinWalletScreen() {
  const navigation = useNavigation<Nav>();
  const qc = useQueryClient();

  const balanceQ = useQuery({ queryKey: ["coin", "balance"], queryFn: getCoinBalance });
  const productsQ = useQuery({ queryKey: ["coin", "products"], queryFn: getCoinProducts });
  const ledgerQ = useQuery({ queryKey: ["coin", "ledger"], queryFn: () => getCoinLedger(30) });

  const charge = useCoinCharge(() => {
    void qc.invalidateQueries({ queryKey: ["coin", "balance"] });
    void qc.invalidateQueries({ queryKey: ["coin", "ledger"] });
  });

  const balance = balanceQ.data?.balance ?? 0;

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
        {/* 잔액 */}
        <View className="mb-6 items-center rounded-2xl border bg-bg-elevated p-6"
              style={{ borderColor: colors.gold.muted }}>
          <Text className="font-sans text-sm text-ink-secondary">내 코인</Text>
          <View className="mt-1 flex-row items-baseline gap-1.5">
            <Text className="font-serif text-4xl text-gold">{won(balance)}</Text>
            <Text className="font-sans text-base text-ink-secondary">코인</Text>
          </View>
          {balanceQ.isPending && <ActivityIndicator className="mt-2" color={colors.gold.primary} />}
        </View>

        {/* 충전팩 */}
        <Text className="mb-2 font-serif text-lg text-ink">코인 충전</Text>
        {!charge.supported && (
          <Text className="mb-3 font-sans text-xs text-ink-muted">
            코인 충전은 앱(iOS·Android)에서만 가능합니다.
          </Text>
        )}
        {charge.error && (
          <Text className="mb-2 font-sans text-xs text-ohaeng-hwa">{charge.error}</Text>
        )}
        <View className="gap-2">
          {(productsQ.data?.charge_packs ?? []).map((p: ChargePack) => (
            <Card key={p.code}>
              <View className="flex-row items-center justify-between">
                <View>
                  <Text className="font-serif text-base text-ink">{won(p.total_coins)} 코인</Text>
                  {p.bonus > 0 && (
                    <Text className="mt-0.5 font-sans text-xs text-gold-light">
                      기본 {won(p.coins)} + 보너스 {won(p.bonus)}
                    </Text>
                  )}
                </View>
                <Pressable
                  onPress={() => charge.buy(p.code as CoinPackCode)}
                  disabled={!charge.supported || charge.status === "purchasing" || charge.status === "verifying"}
                  className="rounded-lg border px-4 py-2 active:opacity-80"
                  style={{
                    borderColor: colors.gold.primary,
                    backgroundColor: "rgba(201,169,97,0.12)",
                    opacity: charge.supported ? 1 : 0.4,
                  }}
                >
                  <Text className="font-sans text-sm text-gold">₩{won(p.price_krw)}</Text>
                </Pressable>
              </View>
            </Card>
          ))}
        </View>
        {(charge.status === "purchasing" || charge.status === "verifying") && (
          <View className="mt-3 flex-row items-center justify-center gap-2">
            <ActivityIndicator color={colors.gold.primary} />
            <Text className="font-sans text-sm text-ink-secondary">
              {charge.status === "verifying" ? "충전 확인 중…" : "결제 진행 중…"}
            </Text>
          </View>
        )}

        {/* 단건 상품 안내 */}
        <Text className="mb-2 mt-8 font-serif text-lg text-ink">코인으로 할 수 있는 것</Text>
        <View className="gap-2">
          {(productsQ.data?.spend_items ?? []).map((s) => (
            <View
              key={s.code}
              className="flex-row items-center justify-between rounded-lg border border-line bg-bg-card px-4 py-3"
            >
              <View className="flex-1 pr-3">
                <Text className="font-sans text-sm text-ink">{s.label}</Text>
                <Text className="mt-0.5 font-sans text-xs text-ink-muted">{s.description}</Text>
              </View>
              <Text className="font-serif text-sm text-gold-light">{won(s.cost)} 코인</Text>
            </View>
          ))}
        </View>

        {/* 거래 내역 */}
        <Text className="mb-2 mt-8 font-serif text-lg text-ink">거래 내역</Text>
        {ledgerQ.isPending ? (
          <ActivityIndicator color={colors.gold.primary} />
        ) : (ledgerQ.data?.transactions.length ?? 0) === 0 ? (
          <Text className="font-sans text-sm text-ink-muted">아직 거래 내역이 없습니다.</Text>
        ) : (
          <View className="gap-1">
            {ledgerQ.data!.transactions.map((t) => (
              <View key={t.id} className="flex-row items-center justify-between border-b border-line py-2">
                <View>
                  <Text className="font-sans text-sm text-ink">
                    {KIND_KO[t.kind] ?? t.kind}
                    {t.memo ? ` · ${t.memo}` : ""}
                  </Text>
                  <Text className="font-sans text-[10px] text-ink-faint">
                    {t.created_at ? t.created_at.slice(0, 10) : ""}
                  </Text>
                </View>
                <Text
                  className="font-serif text-sm"
                  style={{ color: t.amount >= 0 ? colors.gold.primary : colors.text.secondary }}
                >
                  {t.amount >= 0 ? "+" : ""}{won(t.amount)}
                </Text>
              </View>
            ))}
          </View>
        )}

        <View className="mt-8">
          <Button label="요금제(구독) 보기" variant="ghost" onPress={() => navigation.navigate("Plans")} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

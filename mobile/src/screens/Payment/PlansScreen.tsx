/** 가격표 + 플랜 선택 → 결제 시작.
 *
 * BM v2:
 *   - basic 49k / standard 149k / premium 390k / family 590k
 *   - 자동갱신 디폴트 OFF (opt-in 별도 토글)
 *   - 다크패턴 없음: 추천 플랜 강조 X, 사용자 선택 그대로
 *
 * 결제 흐름:
 *   PlansScreen → 플랜·게이트웨이 선택 → CheckoutScreen (WebView/redirect_url)
 *   → 결제 게이트웨이 콜백 → ConfirmScreen
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Alert, Platform, Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { fetchPlans, type Plan, type Provider } from "@/api/payment";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useIap } from "@/hooks/useIap";
import { isIapPlan, isIapSupported } from "@/lib/iap";
import type { RootStackParamList } from "@/navigation/types";
import { colors } from "@/theme";

type Nav = NativeStackNavigationProp<RootStackParamList, "Plans">;

const PROVIDERS: { code: Provider; label: string }[] = [
  { code: "toss", label: "토스페이먼츠" },
  { code: "kakao", label: "카카오페이" },
];

function formatKrw(n: number): string {
  return n.toLocaleString("ko-KR") + "원";
}

export function PlansScreen() {
  const navigation = useNavigation<Nav>();
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<Provider>("toss");
  // BM v2: 자동결제 디폴트 OFF (opt-in). 켜면 카카오페이 정기결제(SID)만 지원.
  const [recurring, setRecurring] = useState(false);

  const { data: plans, isLoading, error } = useQuery({
    queryKey: ["plans"],
    queryFn: fetchPlans,
    staleTime: 5 * 60 * 1000,
  });

  // 네이티브 앱(iOS·Android)에서 basic·standard 는 스토어 자체 결제(IAP) 사용.
  const iap = useIap(() => {
    Alert.alert("구독 완료", "구독이 활성화되었습니다.");
    navigation.goBack();
  });
  const useStorePay =
    isIapSupported && selectedPlan != null && isIapPlan(selectedPlan);

  // 정기결제는 카카오페이 SID 만 지원 → 켜면 결제수단을 카카오로 고정.
  const toggleRecurring = () => {
    setRecurring((prev) => {
      const next = !prev;
      if (next) setSelectedProvider("kakao");
      return next;
    });
  };

  const onProceed = () => {
    if (!selectedPlan) return;
    // 네이티브: 스토어 결제(IAP) — 외부결제(카카오/토스)는 앱 내 디지털 구독에 사용 불가
    if (useStorePay && isIapPlan(selectedPlan)) {
      void iap.buy(selectedPlan);
      return;
    }
    navigation.navigate("Checkout", {
      plan: selectedPlan,
      provider: recurring ? "kakao" : selectedProvider,
      recurring,
    });
  };

  const iapBusy = iap.status === "purchasing" || iap.status === "verifying";

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 40 }}>
        <Text className="mt-4 mb-2 font-serif text-2xl text-ink">자평 플랜</Text>
        <Text className="mb-6 font-sans text-sm text-ink-secondary">
          큰 결정 앞에서, 자평이 함께합니다.{"\n"}
          <Text className="text-ink-muted">자동갱신은 꺼져 있습니다. 필요할 때만 결제하세요.</Text>
        </Text>

        {isLoading && (
          <Card>
            <View className="p-4">
              <Text className="font-sans text-sm text-ink-secondary">가격표 불러오는 중…</Text>
            </View>
          </Card>
        )}

        {error && (
          <Card>
            <View className="p-4">
              <Text className="font-sans text-sm text-state-warning">
                가격표 불러오기 실패. 잠시 후 다시 시도해주세요.
              </Text>
            </View>
          </Card>
        )}

        {plans && (
          <View className="gap-3">
            {(Object.entries(plans) as [Plan, typeof plans[Plan]][])
              .sort((a, b) => a[1].price_krw - b[1].price_krw)
              .map(([code, info]) => {
                const isSelected = selectedPlan === code;
                return (
                  <Pressable
                    key={code}
                    accessibilityRole="radio"
                    accessibilityState={{ selected: isSelected }}
                    onPress={() => setSelectedPlan(code)}
                    className={`rounded-lg border bg-bg-card active:opacity-90 ${
                      isSelected ? "border-gold" : "border-line"
                    }`}
                  >
                    <View className="p-4">
                      <View className="flex-row items-center justify-between">
                        <Text className="font-serif text-lg text-ink">
                          {info.label}
                        </Text>
                        <Text className="font-serif text-lg text-gold">
                          {formatKrw(info.price_krw)}
                          <Text className="font-sans text-sm text-ink-muted">{info.monthly ? " / 월" : ""}</Text>
                        </Text>
                      </View>
                      <Text className="mt-1 font-sans text-sm text-ink-secondary">
                        {info.description}
                      </Text>
                    </View>
                  </Pressable>
                );
              })}
          </View>
        )}

        {/* 정기결제(자동결제) opt-in — BM v2: 디폴트 OFF. 스토어 결제(IAP)는 자동 갱신이므로 숨김 */}
        {selectedPlan && !useStorePay && (
          <Pressable
            accessibilityRole="switch"
            accessibilityState={{ checked: recurring }}
            onPress={toggleRecurring}
            className={`mt-6 flex-row items-center justify-between rounded-lg border bg-bg-card px-4 py-3 active:opacity-90 ${
              recurring ? "border-gold" : "border-line"
            }`}
          >
            <View className="flex-1 pr-3">
              <Text className="font-sans text-sm text-ink">매월 자동결제 (카카오페이 정기결제)</Text>
              <Text className="mt-1 font-sans text-xs text-ink-muted">
                {recurring
                  ? "매월 자동으로 결제됩니다. 마이페이지에서 언제든 해지할 수 있어요."
                  : "꺼두면 매번 직접 결제합니다. 자동결제는 선택사항이에요."}
              </Text>
            </View>
            <View
              className={`h-6 w-11 justify-center rounded-full px-0.5 ${
                recurring ? "bg-gold" : "bg-line"
              }`}
            >
              <View
                className="h-5 w-5 rounded-full bg-bg-base"
                style={{ alignSelf: recurring ? "flex-end" : "flex-start" }}
              />
            </View>
          </Pressable>
        )}

        {/* 게이트웨이 선택 (자동결제 시 카카오페이로 고정). 네이티브 스토어 결제 시 숨김 */}
        {selectedPlan && !recurring && !useStorePay && (
          <View className="mt-6">
            <Text className="mb-2 font-sans text-sm text-ink-muted">결제 수단</Text>
            <View className="flex-row gap-2">
              {PROVIDERS.map((p) => {
                const sel = selectedProvider === p.code;
                return (
                  <Pressable
                    key={p.code}
                    onPress={() => setSelectedProvider(p.code)}
                    className={`flex-1 rounded-lg border px-3 py-3 active:opacity-90 ${
                      sel ? "border-gold bg-bg-card" : "border-line"
                    }`}
                  >
                    <Text
                      className="text-center font-sans text-sm"
                      style={{ color: sel ? colors.gold.primary : colors.text.secondary }}
                    >
                      {p.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        )}

        {useStorePay && (
          <Text className="mt-6 font-sans text-xs text-ink-muted">
            {Platform.OS === "ios" ? "App Store" : "Google Play"} 결제로 진행됩니다.
            구독은 매월 자동 갱신되며, {Platform.OS === "ios" ? "App Store 설정" : "Play 스토어 구독"}에서 언제든 해지할 수 있습니다.
          </Text>
        )}

        {useStorePay && iap.error && (
          <Text className="mt-3 font-sans text-sm text-state-warning">{iap.error}</Text>
        )}

        <View className="mt-8">
          <Button
            label={
              !selectedPlan
                ? "플랜을 선택하세요"
                : useStorePay
                  ? iapBusy
                    ? "처리 중…"
                    : `${selectedPlan.toUpperCase()} 구독하기`
                  : `${selectedPlan.toUpperCase()} ${recurring ? "정기결제 시작" : "결제하기"}`
            }
            onPress={onProceed}
            disabled={!selectedPlan || iapBusy}
          />
        </View>

        {isIapSupported && (
          <Pressable className="mt-3" onPress={() => void iap.restore()}>
            <Text className="text-center font-sans text-xs text-ink-muted underline">
              이전 구매 복원
            </Text>
          </Pressable>
        )}

        <Text className="mt-6 text-center font-sans text-[11px] leading-[16px] text-ink-faint">
          결제 진행 시 <Text className="text-ink-muted">결제·환불 정책</Text>에 동의한 것으로 봅니다.{"\n"}
          7일 내 청약철회 가능 (전자상거래법).
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

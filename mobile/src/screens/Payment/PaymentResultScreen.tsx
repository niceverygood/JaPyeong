/** 결제 confirm + 결과 화면.
 *
 * 흐름:
 *   - route.params.payment_id + (선택) paymentKey/pg_token (게이트웨이 콜백)
 *   - confirmPayment() 호출 → 결과 표시
 *   - 성공: 영수증 링크 + Landing 으로 진입 버튼
 *   - 실패: 메시지 + 재시도 / 환불 안내
 *
 * 게이트웨이 콜백 (네이티브):
 *   - 실 통합 시 deeplink (japyeong://payment/return?payment_id=&paymentKey=)
 *   - 현재는 사용자가 수동 "결제 확인" 누르면 confirm — Mock 어댑터에서는 즉시 성공
 */

import { useNavigation, useRoute, type RouteProp } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useMutation } from "@tanstack/react-query";
import { useEffect } from "react";
import { ActivityIndicator, Linking, Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ApiError } from "@/api/client";
import { confirmPayment } from "@/api/payment";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import type { RootStackParamList } from "@/navigation/types";
import { useAuthStore } from "@/stores/authStore";

type Nav = NativeStackNavigationProp<RootStackParamList, "PaymentResult">;
type Route = RouteProp<RootStackParamList, "PaymentResult">;

function formatKrw(n: number | null): string {
  if (n === null) return "—";
  return n.toLocaleString("ko-KR") + "원";
}

export function PaymentResultScreen() {
  const navigation = useNavigation<Nav>();
  const { params } = useRoute<Route>();

  const mutation = useMutation({
    mutationFn: () =>
      confirmPayment({
        payment_id: params.payment_id,
        extra: {
          ...(params.payment_key ? { paymentKey: params.payment_key } : {}),
          ...(params.pg_token ? { pg_token: params.pg_token } : {}),
        },
      }),
    onSuccess: (data) => {
      // 결제 성공 → JWT 재발급으로 tier 즉시 반영 (KakaoPay/토스 인앱 결제 경로)
      if (data.status === "succeeded" || data.status === "already_succeeded") {
        void useAuthStore.getState().refreshSession();
      }
    },
  });

  useEffect(() => {
    mutation.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const succeeded =
    mutation.data?.status === "succeeded" ||
    mutation.data?.status === "already_succeeded";

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 40, paddingTop: 24 }}>
        <Text className="mb-6 font-serif text-2xl text-ink">결제 결과</Text>

        {mutation.isPending && (
          <Card>
            <View className="items-center p-8">
              <ActivityIndicator />
              <Text className="mt-3 font-sans text-sm text-ink-secondary">
                결제 확인 중…
              </Text>
            </View>
          </Card>
        )}

        {mutation.isError && (
          <Card>
            <View className="p-5">
              <Text className="mb-2 font-serif text-lg text-state-warning">
                결제 확인 실패
              </Text>
              <Text className="mb-3 font-sans text-sm text-ink-secondary">
                {mutation.error instanceof ApiError
                  ? mutation.error.message
                  : "잠시 후 다시 시도해주세요."}
              </Text>
              <Button label="다시 확인" onPress={() => mutation.mutate()} />
              <View className="mt-3">
                <Button
                  label="고객센터 문의"
                  variant="ghost"
                  onPress={() => Linking.openURL("mailto:support@japyeong.com").catch(() => {})}
                />
              </View>
            </View>
          </Card>
        )}

        {succeeded && mutation.data && (
          <Card>
            <View className="p-5">
              <Text className="mb-1 font-serif text-xl text-gold">결제 완료</Text>
              <Text className="mb-4 font-sans text-sm text-ink-secondary">
                자평 구독이 활성화되었습니다.
              </Text>

              <View className="gap-3 rounded-md border border-line bg-bg-elevated p-3">
                <Row label="결제 금액" value={formatKrw(mutation.data.amount_krw)} />
                <Row label="결제 ID" value={`#${mutation.data.payment_id}`} />
                {mutation.data.subscription_id && (
                  <Row label="구독 ID" value={`#${mutation.data.subscription_id}`} />
                )}
              </View>

              {mutation.data.receipt_url && (
                <View className="mt-4">
                  <Pressable onPress={() => Linking.openURL(mutation.data!.receipt_url!).catch(() => {})}>
                    <Text className="font-sans text-sm text-gold underline">
                      영수증 보기
                    </Text>
                  </Pressable>
                </View>
              )}

              <View className="mt-6">
                <Button
                  label="자평 시작"
                  onPress={() => navigation.reset({ index: 0, routes: [{ name: "Landing" }] })}
                />
              </View>
            </View>
          </Card>
        )}

        {mutation.data && mutation.data.status !== "succeeded" && mutation.data.status !== "already_succeeded" && (
          <Card>
            <View className="p-5">
              <Text className="mb-2 font-serif text-lg text-state-warning">
                결제가 완료되지 않았습니다
              </Text>
              <Text className="mb-3 font-sans text-sm text-ink-secondary">
                상태: {mutation.data.status}{"\n"}
                결제가 정상 완료된 경우 잠시 후 다시 확인해주세요.
              </Text>
              <Button label="다시 확인" onPress={() => mutation.mutate()} />
            </View>
          </Card>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row justify-between">
      <Text className="font-sans text-sm text-ink-muted">{label}</Text>
      <Text className="font-sans text-sm text-ink">{value}</Text>
    </View>
  );
}

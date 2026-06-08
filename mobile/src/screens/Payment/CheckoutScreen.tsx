/** 결제 게이트웨이 이동 — redirect_url 발급 + 외부 브라우저 안내.
 *
 * 흐름:
 *   1. createCheckout() → redirect_url 받음
 *   2. 사용자에게 "결제 페이지로 이동합니다" 안내
 *   3. Linking.openURL(redirect_url) — 네이티브: 시스템 브라우저, 웹: 같은 탭
 *   4. 결제 게이트웨이가 success_url 로 콜백 — 딥링크 또는 web 라우팅
 *   5. ConfirmScreen 이 payment_id + extra (paymentKey/pg_token) 로 confirm 호출
 *
 * 보안:
 *   - success_url / fail_url 은 자평 도메인만 허용 (백엔드는 검증 안 하지만 모바일에서 자체 가드)
 *   - 게이트웨이 페이지에서 사용자가 결제 완료해야 confirm 가능
 */

import { useNavigation, useRoute, type RouteProp } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ActivityIndicator, Linking, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ApiError } from "@/api/client";
import { createCheckout } from "@/api/payment";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import type { RootStackParamList } from "@/navigation/types";

type Nav = NativeStackNavigationProp<RootStackParamList, "Checkout">;
type Route = RouteProp<RootStackParamList, "Checkout">;

const SUCCESS_URL = "https://ja-pyeong.vercel.app/payment/success";
const FAIL_URL = "https://ja-pyeong.vercel.app/payment/fail";

export function CheckoutScreen() {
  const navigation = useNavigation<Nav>();
  const { params } = useRoute<Route>();
  const [opened, setOpened] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      createCheckout({
        plan: params.plan,
        provider: params.provider,
        success_url: SUCCESS_URL,
        fail_url: FAIL_URL,
      }),
  });

  // 자동 1회 호출 (mount 시)
  useEffect(() => {
    mutation.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openGateway = async () => {
    const url = mutation.data?.redirect_url;
    if (!url) return;
    try {
      await Linking.openURL(url);
      setOpened(true);
    } catch (e) {
      // open 실패 시 사용자에게 URL 복사 안내
      mutation.reset();
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 40, paddingTop: 24 }}>
        <Text className="mb-2 font-serif text-2xl text-ink">결제 진행</Text>
        <Text className="mb-6 font-sans text-sm text-ink-secondary">
          {params.plan.toUpperCase()} · {labelOfProvider(params.provider)}
        </Text>

        {mutation.isPending && (
          <Card>
            <View className="items-center p-6">
              <ActivityIndicator />
              <Text className="mt-2 font-sans text-sm text-ink-secondary">
                결제 페이지 준비 중…
              </Text>
            </View>
          </Card>
        )}

        {mutation.isError && (
          <Card>
            <View className="p-4">
              <Text className="mb-2 font-sans text-sm text-state-warning">
                결제 시작 실패
              </Text>
              <Text className="mb-3 font-sans text-xs text-ink-muted">
                {mutation.error instanceof ApiError
                  ? mutation.error.message
                  : "잠시 후 다시 시도해주세요."}
              </Text>
              <Button label="다시 시도" onPress={() => mutation.mutate()} />
            </View>
          </Card>
        )}

        {mutation.data && (
          <Card>
            <View className="p-4">
              <Text className="mb-2 font-sans text-sm text-ink-muted">주문번호</Text>
              <Text className="mb-4 font-sans text-base text-ink">
                {mutation.data.order_id}
              </Text>

              <Text className="mb-3 font-sans text-sm text-ink-secondary">
                {opened
                  ? "결제를 완료하시면 자동으로 자평으로 돌아옵니다.\n돌아오지 않으면 아래 '결제 확인' 을 눌러주세요."
                  : "외부 결제 페이지로 이동합니다.\n결제 완료 후 자평 앱으로 돌아오세요."}
              </Text>

              {!opened ? (
                <Button label="결제 페이지 열기" onPress={openGateway} />
              ) : (
                <View className="gap-3">
                  <Button
                    label="결제 확인"
                    onPress={() =>
                      navigation.navigate("PaymentResult", {
                        payment_id: mutation.data.payment_id,
                      })
                    }
                  />
                  <Button
                    label="결제 페이지 다시 열기"
                    variant="ghost"
                    onPress={openGateway}
                  />
                </View>
              )}
            </View>
          </Card>
        )}

        <View className="mt-8">
          <Button
            label="플랜으로 돌아가기"
            variant="ghost"
            onPress={() => navigation.goBack()}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function labelOfProvider(p: string): string {
  if (p === "toss") return "토스페이먼츠";
  if (p === "kakao") return "카카오페이";
  return "결제";
}

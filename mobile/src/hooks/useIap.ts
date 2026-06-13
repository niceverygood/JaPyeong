/** useIap — 네이티브 인앱결제 구매 흐름 훅.
 *
 * 책임:
 *   - 구매 성공/실패 리스너 등록 (purchaseUpdated / purchaseError)
 *   - 구매 성공 시 영수증을 서버(/v1/payment/iap/verify)에 보내 검증·구독 활성화
 *   - 검증 성공 후 finishTransaction (필수 — 누락 시 스토어가 환불 처리)
 *   - buy(plan) / restore() / 상태(status) 제공
 *
 * 웹에서는 동작하지 않음 (isIapSupported=false) — 화면에서 분기.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Platform } from "react-native";
import {
  purchaseErrorListener,
  purchaseUpdatedListener,
  type PurchaseError,
  type SubscriptionPurchase,
} from "react-native-iap";

import { verifyIapPurchase, type Plan } from "@/api/payment";
import { useAuthStore } from "@/stores/authStore";
import {
  ANDROID_PACKAGE,
  completeTransaction,
  getExistingPurchases,
  isIapPlan,
  isIapSupported,
  requestPlanPurchase,
  skuToPlan,
} from "@/lib/iap";

export type IapStatus = "idle" | "purchasing" | "verifying" | "success" | "error";

interface UseIapResult {
  supported: boolean;
  status: IapStatus;
  error: string | null;
  buy: (plan: Plan) => Promise<void>;
  restore: () => Promise<boolean>;
}

export function useIap(onActivated?: () => void): UseIapResult {
  const [status, setStatus] = useState<IapStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const onActivatedRef = useRef(onActivated);
  onActivatedRef.current = onActivated;

  // 구매 성공 → 서버 검증 → 완료 처리
  const handlePurchase = useCallback(async (purchase: SubscriptionPurchase) => {
    const sku = purchase.productId;
    const plan = skuToPlan(sku);
    if (!plan) return;
    const receipt =
      Platform.OS === "ios"
        ? purchase.transactionReceipt
        : purchase.purchaseToken;
    if (!receipt) {
      setStatus("error");
      setError("영수증 정보를 가져오지 못했습니다.");
      return;
    }
    try {
      setStatus("verifying");
      await verifyIapPurchase({
        platform: Platform.OS === "ios" ? "ios" : "android",
        plan,
        product_id: sku,
        receipt,
        transaction_id: purchase.transactionId,
        package_name: Platform.OS === "android" ? ANDROID_PACKAGE : undefined,
      });
      // 서버 검증 성공 후에만 거래 종료
      await completeTransaction(purchase);
      // 구독 활성화됨 → JWT 재발급으로 tier 즉시 반영 (한도·심층모델 잠금 해제)
      await useAuthStore.getState().refreshSession();
      setStatus("success");
      onActivatedRef.current?.();
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "결제 검증에 실패했습니다.");
    }
  }, []);

  useEffect(() => {
    if (!isIapSupported) return;
    const updateSub = purchaseUpdatedListener((p) => {
      void handlePurchase(p as SubscriptionPurchase);
    });
    const errorSub = purchaseErrorListener((err: PurchaseError) => {
      // 사용자가 취소한 경우는 조용히 idle 로
      if (err.code === "E_USER_CANCELLED") {
        setStatus("idle");
        return;
      }
      setStatus("error");
      setError(err.message ?? "결제 중 오류가 발생했습니다.");
    });
    return () => {
      updateSub.remove();
      errorSub.remove();
    };
  }, [handlePurchase]);

  const buy = useCallback(async (plan: Plan) => {
    if (!isIapSupported || !isIapPlan(plan)) return;
    setError(null);
    setStatus("purchasing");
    try {
      await requestPlanPurchase(plan);
      // 이후 결과는 purchaseUpdatedListener 로
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "결제창을 열 수 없습니다.");
    }
  }, []);

  const restore = useCallback(async (): Promise<boolean> => {
    if (!isIapSupported) return false;
    setError(null);
    setStatus("verifying");
    try {
      const purchases = await getExistingPurchases();
      const target = purchases.find((p) => skuToPlan(p.productId));
      if (!target) {
        setStatus("idle");
        return false;
      }
      await handlePurchase(target);
      return true;
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "구매 복원에 실패했습니다.");
      return false;
    }
  }, [handlePurchase]);

  return { supported: isIapSupported, status, error, buy, restore };
}

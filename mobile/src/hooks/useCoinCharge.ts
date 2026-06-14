/** useCoinCharge — 코인 충전팩(소비성 IAP) 구매 흐름 훅.
 *
 * 구매 성공 → /v1/coins/charge/verify 로 영수증 검증·코인 적립 → finishTransaction(consumable).
 * 구독(useIap)과 리스너가 공존해도 isCoinPack 으로 코인팩만 처리(구독 결제는 무시).
 * 웹은 미지원(isIapSupported=false).
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Platform } from "react-native";
import {
  purchaseErrorListener,
  purchaseUpdatedListener,
  type ProductPurchase,
  type PurchaseError,
} from "react-native-iap";

import { verifyCoinCharge } from "@/api/coins";
import {
  ANDROID_PACKAGE,
  completeConsumable,
  isCoinPack,
  isIapSupported,
  requestCoinPurchase,
  type CoinPackCode,
} from "@/lib/iap";

export type CoinChargeStatus = "idle" | "purchasing" | "verifying" | "success" | "error";

export function useCoinCharge(onCredited?: (balance: number) => void) {
  const [status, setStatus] = useState<CoinChargeStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const cbRef = useRef(onCredited);
  cbRef.current = onCredited;

  const handle = useCallback(async (purchase: ProductPurchase) => {
    const sku = purchase.productId;
    if (!isCoinPack(sku)) return; // 구독 등 다른 결제는 무시
    const receipt =
      Platform.OS === "ios"
        ? purchase.transactionReceipt
        : (purchase as { purchaseToken?: string }).purchaseToken;
    if (!receipt || !purchase.transactionId) {
      setStatus("error");
      setError("영수증 정보를 가져오지 못했습니다.");
      return;
    }
    try {
      setStatus("verifying");
      const res = await verifyCoinCharge({
        platform: Platform.OS === "ios" ? "ios" : "android",
        product_id: sku,
        receipt,
        transaction_id: purchase.transactionId,
        package_name: Platform.OS === "android" ? ANDROID_PACKAGE : undefined,
      });
      await completeConsumable(purchase); // 소비성 완료 — 미호출 시 재구매 불가
      setStatus("success");
      cbRef.current?.(res.balance);
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "충전 검증에 실패했습니다.");
    }
  }, []);

  useEffect(() => {
    if (!isIapSupported) return;
    const updateSub = purchaseUpdatedListener((p) => {
      void handle(p as ProductPurchase);
    });
    const errorSub = purchaseErrorListener((err: PurchaseError) => {
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
  }, [handle]);

  const buy = useCallback(async (code: CoinPackCode) => {
    if (!isIapSupported) return;
    setError(null);
    setStatus("purchasing");
    try {
      await requestCoinPurchase(code);
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "결제창을 열 수 없습니다.");
    }
  }, []);

  return { supported: isIapSupported, status, error, buy };
}

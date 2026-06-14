/** 네이티브 인앱결제(IAP) — Apple App Store / Google Play.
 *
 * 정책: iOS·Android 앱 안에서 파는 디지털 구독(basic·standard)은
 *       반드시 스토어 자체 결제(StoreKit / Play Billing)를 사용한다.
 *       (카카오페이/토스 등 외부결제는 앱 내 디지털 구독에 사용 불가 — 심사 반려)
 *       웹(ja-pyeong.vercel.app)은 카카오페이 정기결제를 그대로 사용한다.
 *
 * 흐름:
 *   1. ensureConnection() → 스토어 연결
 *   2. loadSubscriptions() → 가격·상품 정보 로드
 *   3. requestPlanPurchase(plan) → 스토어 결제창
 *   4. purchaseUpdatedListener (useIap 훅) → 영수증을 서버에 검증 요청
 *      → finishTransaction → 구독 활성화
 *
 * 스토어 상품 ID(아래 IAP_SKUS)는 App Store Connect / Play Console 에
 * 동일한 ID의 "자동 갱신 구독" 상품으로 미리 등록해야 한다.
 */

import { Platform } from "react-native";
import {
  endConnection,
  finishTransaction,
  getAvailablePurchases,
  getProducts,
  getSubscriptions,
  initConnection,
  requestPurchase,
  requestSubscription,
  type Product,
  type ProductPurchase,
  type Subscription,
  type SubscriptionPurchase,
} from "react-native-iap";

import type { Plan } from "@/api/payment";

/** 스토어에 등록할 구독 상품 ID (iOS·Android 동일하게 생성) */
export const IAP_SKUS = {
  basic: "japyeong_basic_monthly",
  standard: "japyeong_standard_monthly",
} as const;

export type IapPlan = keyof typeof IAP_SKUS;

export const ALL_SKUS: string[] = Object.values(IAP_SKUS);

/** Android 패키지명 (서버 영수증 검증용) — app.json android.package 와 일치 */
export const ANDROID_PACKAGE = "com.japyeong.app";

const SKU_TO_PLAN: Record<string, Plan> = {
  [IAP_SKUS.basic]: "basic",
  [IAP_SKUS.standard]: "standard",
};

export function skuToPlan(sku: string): Plan | null {
  return SKU_TO_PLAN[sku] ?? null;
}

/** 네이티브(iOS·Android)에서만 IAP 사용. 웹은 카카오페이. */
export const isIapSupported = Platform.OS === "ios" || Platform.OS === "android";

/** 해당 플랜이 IAP(스토어 결제) 대상인지. premium·family(전화 자문)는 제외. */
export function isIapPlan(plan: Plan): plan is IapPlan {
  return plan === "basic" || plan === "standard";
}

let connected = false;

export async function ensureConnection(): Promise<void> {
  if (connected || !isIapSupported) return;
  await initConnection();
  connected = true;
}

export async function closeConnection(): Promise<void> {
  if (!connected) return;
  await endConnection();
  connected = false;
}

/** 스토어 구독 상품(가격·라벨) 로드 */
export async function loadSubscriptions(): Promise<Subscription[]> {
  await ensureConnection();
  return getSubscriptions({ skus: ALL_SKUS });
}

/** 구독 결제창 요청. 결과 구매건은 purchaseUpdatedListener 로 전달된다. */
export async function requestPlanPurchase(plan: IapPlan): Promise<void> {
  await ensureConnection();
  const sku = IAP_SKUS[plan];

  if (Platform.OS === "android") {
    // Android 구독은 offerToken 이 필요 (SubscriptionAndroid 에만 존재)
    const subs = await getSubscriptions({ skus: [sku] });
    const androidSub = subs[0] as unknown as
      | { subscriptionOfferDetails?: { offerToken: string }[] }
      | undefined;
    const offerToken = androidSub?.subscriptionOfferDetails?.[0]?.offerToken;
    await requestSubscription({
      sku,
      ...(offerToken
        ? { subscriptionOffers: [{ sku, offerToken }] }
        : {}),
    });
    return;
  }

  // iOS
  await requestSubscription({ sku });
}

/** 복원: 이미 구독한 구매 내역을 다시 불러온다(기기 변경·재설치 시). */
export async function getExistingPurchases(): Promise<SubscriptionPurchase[]> {
  await ensureConnection();
  const purchases = await getAvailablePurchases();
  return purchases as SubscriptionPurchase[];
}

/** 거래 완료 처리 (서버 검증 성공 후 호출 — 미호출 시 환불·재청구 위험) */
export async function completeTransaction(
  purchase: SubscriptionPurchase,
): Promise<void> {
  await finishTransaction({ purchase, isConsumable: false });
}


// ── 코인 충전팩 (소비성 consumable) ──────────────────────────
// 스토어 product_id = 백엔드 coin_catalog 코드. App Store/Play 에 '소비성' 상품으로 등록.
export const COIN_PACK_SKUS = [
  "coin_10000",
  "coin_30000",
  "coin_50000",
  "coin_100000",
] as const;

export type CoinPackCode = (typeof COIN_PACK_SKUS)[number];

export function isCoinPack(sku: string): sku is CoinPackCode {
  return (COIN_PACK_SKUS as readonly string[]).includes(sku);
}

/** 코인 충전팩 상품(가격·라벨) 로드 */
export async function loadCoinProducts(): Promise<Product[]> {
  await ensureConnection();
  return getProducts({ skus: [...COIN_PACK_SKUS] });
}

/** 코인 충전팩 결제창 요청 (소비성). 결과는 purchaseUpdatedListener 로 전달. */
export async function requestCoinPurchase(code: CoinPackCode): Promise<void> {
  await ensureConnection();
  if (Platform.OS === "android") {
    await requestPurchase({ skus: [code] });
    return;
  }
  await requestPurchase({ sku: code });
}

/** 코인 충전 거래 완료 (소비성 — isConsumable=true 라야 재구매 가능) */
export async function completeConsumable(
  purchase: ProductPurchase,
): Promise<void> {
  await finishTransaction({ purchase, isConsumable: true });
}

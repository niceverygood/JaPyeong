/** 결제 API 클라이언트.
 *
 * 백엔드: src/api/v1/payment.py
 */

import { get, patch, post } from "./client";

export type Plan = "basic" | "standard" | "premium" | "family";
export type Provider = "toss" | "kakao" | "mock";

export interface PlanInfo {
  price_krw: number;
  label: string;
  monthly: boolean;
  description: string;
}

export type PlansResponse = Record<Plan, PlanInfo>;

export interface CheckoutRequest {
  plan: Plan;
  provider: Provider;
  success_url: string;
  fail_url: string;
  channel?: string;
  tm_partner_code?: string;
  /** 정기결제(자동청구). 카카오페이 SID 발급 + 자동갱신 opt-in. */
  recurring?: boolean;
}

export interface CheckoutResponse {
  payment_id: number;
  subscription_id: number;
  order_id: string;
  redirect_url: string;
  provider: string;
  provider_session_id: string;
  recurring: boolean;
}

export interface ConfirmRequest {
  payment_id: number;
  extra?: Record<string, string>;
}

export interface ConfirmResponse {
  payment_id: number;
  subscription_id: number | null;
  status: string;
  amount_krw: number | null;
  provider_tx_id: string | null;
  receipt_url: string | null;
}

export function fetchPlans(): Promise<PlansResponse> {
  return get<PlansResponse>("/v1/payment/plans");
}

export function createCheckout(body: CheckoutRequest): Promise<CheckoutResponse> {
  return post<CheckoutResponse>("/v1/payment/checkout", body);
}

export function confirmPayment(body: ConfirmRequest): Promise<ConfirmResponse> {
  return post<ConfirmResponse>("/v1/payment/confirm", body);
}

export function setAutorenew(subscription_id: number, enabled: boolean): Promise<{ subscription_id: number; autorenew: boolean }> {
  return patch("/v1/payment/autorenew", { subscription_id, enabled });
}

export interface CancelRecurringResponse {
  subscription_id: number;
  status: string;
  reason: string;
  access_until: string | null;
}

/** 정기결제 해지 — 카카오 SID 폐기. 구독은 access_until 까지 유지. */
export function cancelRecurring(
  subscription_id: number,
  reason?: string,
): Promise<CancelRecurringResponse> {
  return post<CancelRecurringResponse>("/v1/payment/recurring/cancel", {
    subscription_id,
    reason,
  });
}

// ── 네이티브 인앱결제(IAP) 영수증 검증 ─────────────────────────
// iOS: App Store 영수증 / Android: Play 구매토큰을 서버에 보내 검증·구독 활성화.
export interface IapVerifyRequest {
  platform: "ios" | "android";
  plan: Plan;
  product_id: string;
  /** iOS: transactionReceipt(base64) / Android: purchaseToken */
  receipt: string;
  transaction_id?: string;
  /** Android 패키지명 (검증용) */
  package_name?: string;
}

/** 스토어 영수증을 서버에서 검증하고 구독을 활성화한다. */
export function verifyIapPurchase(
  body: IapVerifyRequest,
): Promise<ConfirmResponse> {
  return post<ConfirmResponse>("/v1/payment/iap/verify", body);
}

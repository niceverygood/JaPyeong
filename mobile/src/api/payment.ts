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
}

export interface CheckoutResponse {
  payment_id: number;
  subscription_id: number;
  order_id: string;
  redirect_url: string;
  provider: string;
  provider_session_id: string;
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

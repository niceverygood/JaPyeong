/** /v1/coins API — 선충전 지갑 + 단건 상품 (ARPU). */

import { get, post } from "./client";
import type { BirthInput } from "./types";

export interface ChargePack {
  code: string;
  price_krw: number;
  coins: number;
  bonus: number;
  total_coins: number;
  label: string;
}

export interface SpendItem {
  code: string;
  cost: number;
  label: string;
  kind: string;
  description: string;
}

export interface CoinProducts {
  charge_packs: ChargePack[];
  spend_items: SpendItem[];
}

export interface CoinTxn {
  id: number;
  kind: string; // charge|bonus|spend|refund|expire|adjust
  amount: number;
  balance_after: number;
  item_code: string | null;
  memo: string | null;
  created_at: string | null;
}

export interface SpendContent {
  answer?: string;
  basis?: string;
  perspective?: string;
  timing?: string;
  cautions?: string[];
  citations?: { source: string; volume?: string | null }[];
  contested?: string[];
  confidence?: string;
  model?: string;
  flags?: string[];
  // decision 전용
  option_a_view?: string;
  option_b_view?: string;
  comparison?: string;
  lean?: string;
  lean_reason?: string;
}

export interface SpendResponse {
  item_code: string;
  balance: number;
  charged: number;
  content: SpendContent;
}

export interface SpendRequest {
  item_code: string;
  birth: BirthInput;
  question?: string;
  option_a?: { title: string; description: string };
  option_b?: { title: string; description: string };
  context?: string;
}

export function getCoinProducts(): Promise<CoinProducts> {
  return get<CoinProducts>("/v1/coins/products");
}

export function getCoinBalance(): Promise<{ balance: number }> {
  return get<{ balance: number }>("/v1/coins/balance");
}

export function getCoinLedger(limit = 50): Promise<{ transactions: CoinTxn[] }> {
  return get<{ transactions: CoinTxn[] }>(`/v1/coins/ledger?limit=${limit}`);
}

export function verifyCoinCharge(body: {
  platform: "ios" | "android";
  product_id: string;
  receipt: string;
  transaction_id?: string;
  package_name?: string;
}): Promise<{ balance: number; credited: number; duplicate: boolean }> {
  return post("/v1/coins/charge/verify", body);
}

export function spendCoins(body: SpendRequest): Promise<SpendResponse> {
  return post<SpendResponse>("/v1/coins/spend", body);
}

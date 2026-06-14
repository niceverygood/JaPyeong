/** /v1/chat API + TanStack mutation. */

import { useMutation } from "@tanstack/react-query";

import { post } from "./client";
import type { BirthInput } from "./types";

export interface Citation {
  source: string;
  volume?: string | null;
}

export type Confidence = "high" | "medium" | "low";

export interface ChatResponse {
  answer: string;
  basis: string;
  perspective: string;
  timing: string;
  cautions: string[];
  citations: Citation[];
  contested: string[]; // 학파별 견해 차이
  confidence: Confidence;
  follow_up_suggestions: string[];
  flags: string[];
  model: string;
}

export interface ChatRequest {
  birth: BirthInput;
  question: string;
}

export function sendChat(req: ChatRequest): Promise<ChatResponse> {
  return post<ChatResponse>("/v1/chat", req);
}

export function useChat() {
  return useMutation({
    mutationFn: sendChat,
  });
}

// ── 무료 맛보기(teaser) — 결정론 '내 한 줄' (전환 퍼널) ──────────
export interface TeaserResponse {
  hook: string;
  flow: string;
  covers: string[];
  note: string;
  unlock: {
    free: string;
    coin_item: string;
    coin_cost: number;
    coin_label: string;
    subscription_label: string;
  };
}

export interface TeaserRequest {
  birth: BirthInput;
  question?: string;
}

export function fetchTeaser(req: TeaserRequest): Promise<TeaserResponse> {
  return post<TeaserResponse>("/v1/chat/teaser", req);
}

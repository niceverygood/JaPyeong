/** /v1/decision API + TanStack mutation — 결정 도우미 A/B. */

import { useMutation } from "@tanstack/react-query";

import type { Citation, Confidence } from "./chat";
import { post } from "./client";
import type { BirthInput } from "./types";

export type Lean = "A" | "B" | "balanced";

export interface OptionInput {
  title: string;
  description: string;
}

export interface DecisionRequest {
  birth: BirthInput;
  option_a: OptionInput;
  option_b: OptionInput;
  context?: string | null;
}

export interface DecisionResponse {
  option_a_view: string;
  option_b_view: string;
  comparison: string;
  lean: Lean;
  lean_reason: string;
  answer: string;
  basis: string;
  perspective: string;
  timing: string;
  cautions: string[];
  citations: Citation[];
  contested: string[];
  confidence: Confidence;
  follow_up_suggestions: string[];
  flags: string[];
  model: string;
}

export function sendDecision(req: DecisionRequest): Promise<DecisionResponse> {
  return post<DecisionResponse>("/v1/decision", req);
}

export function useDecision() {
  return useMutation({
    mutationFn: sendDecision,
  });
}

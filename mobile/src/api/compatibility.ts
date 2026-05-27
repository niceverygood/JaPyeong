/** /v1/compatibility API + TanStack mutation. */

import { useMutation } from "@tanstack/react-query";

import { post } from "./client";
import type { Citation, Confidence } from "./chat";
import type { BirthInput, Relation } from "./types";

export type RelationshipType =
  | "romantic"
  | "marriage"
  | "business"
  | "family"
  | "general";

export interface DayMasterPair {
  day_master_a: string;
  day_master_b: string;
  element_a: string;
  element_b: string;
  a_to_b: string;
  b_to_a: string;
  dynamic: string; // 비화 / A생B / B생A / A극B / B극A
}

export interface ElementCombined {
  mok: number;
  hwa: number;
  to: number;
  geum: number;
  su: number;
  total: number;
  balance_a: number;
  balance_b: number;
  balance_combined: number;
  balance_gain: number;
}

export interface CompatAnalysis {
  cross_relations: Relation[];
  day_master_pair: DayMasterPair;
  element_combined: ElementCombined;
  strong_bonds_count: number;
  conflicts_count: number;
  notes: string[];
}

export interface CompatRequest {
  birth_a: BirthInput;
  birth_b: BirthInput;
  relationship_type: RelationshipType;
  question?: string | null;
  label_a?: string | null;
  label_b?: string | null;
}

export interface CompatResponse {
  analysis: CompatAnalysis;
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
  relationship_type: RelationshipType;
}

export function sendCompatibility(req: CompatRequest): Promise<CompatResponse> {
  return post<CompatResponse>("/v1/compatibility", req);
}

export function useCompatibility() {
  return useMutation({
    mutationFn: sendCompatibility,
  });
}

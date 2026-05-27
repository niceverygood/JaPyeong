/** /v1/date-selection API + TanStack mutation. */

import { useMutation } from "@tanstack/react-query";

import { post } from "./client";
import type { BirthInput, Pillar } from "./types";

export type EventType = "marriage" | "moving" | "business" | "contract" | "general";

export interface CandidateDate {
  date: string; // ISO yyyy-mm-dd
  day_pillar: Pillar;
  score: number; // -5..+5
  label: string; // 대길/길/평/주의/흉
  ten_god: string;
  reasons: string[];
}

export interface DateSelectionRequest {
  birth: BirthInput;
  start: string; // yyyy-mm-dd
  end: string;
  event_type: EventType;
  top_n?: number;
}

export interface DateSelectionResponse {
  event_type: EventType;
  start: string;
  end: string;
  candidates: CandidateDate[];
  note: string;
}

export function sendDateSelection(
  req: DateSelectionRequest,
): Promise<DateSelectionResponse> {
  return post<DateSelectionResponse>("/v1/date-selection", req);
}

export function useDateSelection() {
  return useMutation({
    mutationFn: sendDateSelection,
  });
}

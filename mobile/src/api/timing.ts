/** /v1/timing API — 결정 타이밍 코치(시그니처). */

import { useMutation } from "@tanstack/react-query";

import { post } from "./client";
import type { CandidateDate, EventType } from "./dateSelection";
import type { BirthInput } from "./types";

export type { EventType, CandidateDate };

export interface Citation {
  source: string;
  volume?: string | null;
}

export interface TimingRequest {
  birth: BirthInput;
  start: string; // yyyy-mm-dd
  end: string;
  event_type: EventType;
  top_n?: number;
}

export interface TimingResponse {
  event_type: EventType;
  start: string;
  end: string;
  calendar: CandidateDate[];
  best: CandidateDate[];
  avoid: CandidateDate[];
  recommendation: string;
  perspective: string;
  timing: string;
  cautions: string[];
  citations: Citation[];
  contested: string[];
  confidence: string;
  model: string;
  note: string;
}

export function sendTiming(req: TimingRequest): Promise<TimingResponse> {
  return post<TimingResponse>("/v1/timing", req);
}

export function useTiming() {
  return useMutation({ mutationFn: sendTiming });
}

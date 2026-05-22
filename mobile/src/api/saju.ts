/** /v1/saju API 호출 + TanStack Query 훅. */

import { useQuery } from "@tanstack/react-query";

import { get, post } from "./client";
import type { BirthInput, LuckResponse, NatalResponse } from "./types";

export function analyzeSaju(birth: BirthInput): Promise<NatalResponse> {
  return post<NatalResponse>("/v1/saju/analyze", birth);
}

export function fetchLuck(on?: string): Promise<LuckResponse> {
  const qs = on ? `?on=${on}` : "";
  return get<LuckResponse>(`/v1/saju/luck${qs}`);
}

/** 출생정보로 원국 분석. birth가 없으면 비활성. */
export function useAnalyzeSaju(birth: BirthInput | null) {
  return useQuery({
    queryKey: ["saju", "analyze", birth],
    queryFn: () => analyzeSaju(birth as BirthInput),
    enabled: birth != null,
    staleTime: Infinity, // 같은 출생정보는 항상 같은 결과
  });
}

export function useLuck(on?: string) {
  return useQuery({
    queryKey: ["saju", "luck", on ?? "today"],
    queryFn: () => fetchLuck(on),
  });
}

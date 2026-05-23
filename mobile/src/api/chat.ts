/** /v1/chat API + TanStack mutation. */

import { useMutation } from "@tanstack/react-query";

import { post } from "./client";
import type { BirthInput } from "./types";

export interface Citation {
  source: string;
  volume?: string | null;
}

export interface ChatResponse {
  answer: string;
  basis: string;
  citations: Citation[];
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

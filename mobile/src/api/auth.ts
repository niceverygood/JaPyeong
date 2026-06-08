/** 회원 가입·로그인·OAuth·탈퇴 API.
 *
 * 백엔드: src/api/v1/auth.py
 */

import { del, get, post } from "./client";

export interface AuthResponse {
  user_id: number;
  token: string;
  tier: string;
  is_new: boolean;
}

export interface MeResponse {
  user_id: number;
  email: string | null;
  name: string | null;
  tier: string;
}

export interface SignupBody {
  email: string;
  password: string;
  name?: string;
  phone?: string;
  marketing_consent?: boolean;
}

export interface LoginBody {
  email: string;
  password: string;
}

export interface OAuthBody {
  provider: "kakao" | "apple" | "google";
  subject: string;
  email?: string;
  name?: string;
}

export function signup(body: SignupBody): Promise<AuthResponse> {
  return post<AuthResponse>("/v1/auth/signup", body);
}

export function login(body: LoginBody): Promise<AuthResponse> {
  return post<AuthResponse>("/v1/auth/login", body);
}

export function oauthLogin(body: OAuthBody): Promise<AuthResponse> {
  return post<AuthResponse>("/v1/auth/oauth", body);
}

export function refreshToken(): Promise<AuthResponse> {
  return post<AuthResponse>("/v1/auth/refresh", {});
}

export function fetchMe(): Promise<MeResponse> {
  return get<MeResponse>("/v1/auth/me");
}

export function deleteMe(): Promise<void> {
  return del<void>("/v1/auth/me");
}

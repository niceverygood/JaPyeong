/** 백엔드 /v1/saju 응답·요청 타입 (backend NatalResponse 등과 1:1). */

export type Gender = "M" | "F";
export type Calendar = "solar" | "lunar";

export interface BirthInput {
  name?: string;
  gender: Gender;
  calendar: Calendar;
  year: number;
  month: number;
  day: number;
  hour?: number | null;
  minute?: number | null;
  is_leap_month?: boolean;
  birth_place?: string | null;
  longitude?: number | null;
  latitude?: number | null;
  timezone?: string;
}

export interface Pillar {
  gan: string;
  ji: string;
}

export interface FourPillars {
  year: Pillar;
  month: Pillar;
  day: Pillar;
  hour: Pillar | null;
}

export interface TenGodsCount {
  bi_gyeon: number;
  gyeop_jae: number;
  sik_sin: number;
  sang_gwan: number;
  jeong_jae: number;
  pyeon_jae: number;
  jeong_gwan: number;
  pyeon_gwan: number;
  jeong_in: number;
  pyeon_in: number;
}

export interface FiveElements {
  mok: number;
  hwa: number;
  to: number;
  geum: number;
  su: number;
  total: number;
  dominant: string;
  weakest: string;
  balance: number;
}

export interface Relation {
  type: string;
  members: string[];
  positions: string[];
}

export interface DaewoonPeriod {
  sequence: number;
  start_age: number;
  gan: string;
  ji: string;
}

export interface Daewoon {
  direction: "forward" | "backward";
  start_age: number;
  periods: DaewoonPeriod[];
}

export interface NatalResponse {
  pillars: FourPillars;
  day_master: string;
  day_master_element: string;
  ten_gods: TenGodsCount;
  five_elements: FiveElements;
  relations: Relation[];
  daewoon: Daewoon;
}

export interface LuckResponse {
  date: string;
  se_un: Pillar;
  wol_un: Pillar;
  il_un: Pillar;
}

/**
 * 자평 디자인 시스템 — 컬러 토큰
 * assets/design/mobile-screens.html 에서 추출한 팔레트 기반.
 * 동양적 절제 + 전문성/신뢰감 (다크 톤 + 골드 포인트).
 */

export const colors = {
  // 배경
  bg: {
    base: "#0F1419", // 앱 기본 배경 (딥 네이비-블랙)
    elevated: "#1A2129", // 카드/시트
    card: "#2A251F", // 따뜻한 카드 (사주판 등)
  },

  // 포인트 (골드)
  gold: {
    primary: "#C9A961",
    light: "#D4B574",
    muted: "#8B7A4D",
  },

  // 강조 (테라코타/브라운)
  accent: {
    terracotta: "#C96442",
    clay: "#C97B5A",
    brown: "#8B5A3C",
  },

  // 텍스트
  text: {
    primary: "#F5EFE0", // 크림 화이트
    secondary: "#B8B0A0",
    muted: "#6B6357",
  },

  // 오행(五行) — 사주 차트/십성 색상
  ohaeng: {
    mok: "#7A9B6E", // 木 목 (청)
    hwa: "#A04545", // 火 화 (적)
    to: "#8B7A4D", // 土 토 (황)
    geum: "#D4B574", // 金 금 (백/금)
    su: "#4A6FA5", // 水 수 (흑/청)
  },

  // 상태
  state: {
    positive: "#7A9B6E",
    caution: "#C9A961",
    warning: "#A04545",
    info: "#4A6FA5",
  },

  line: "#2E3640", // 구분선
} as const;

export type Colors = typeof colors;

/**
 * 자평 디자인 시스템 — 타이포그래피 토큰
 * 명조(본명조/Noto Serif KR)로 격조·전통, Pretendard로 본문 가독성.
 */

// 웹은 global.css에서 CDN으로 로드. 네이티브는 추후 expo-font 추가 시 동일 키로 등록.
export const fontFamily = {
  serif:
    '"Noto Serif KR", "Apple SD Gothic Neo", "Nanum Myeongjo", Batang, serif',
  sans:
    '"Pretendard Variable", Pretendard, "Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif',
} as const;

export const fontSize = {
  display: 32, // 사주 한자 대형 표시
  h1: 24,
  h2: 20,
  h3: 17,
  body: 15,
  caption: 13,
  micro: 11,
} as const;

export const lineHeight = {
  tight: 1.2,
  normal: 1.5,
  relaxed: 1.7, // 자문 본문 (긴 글)
} as const;

export const fontWeight = {
  regular: "400",
  medium: "500",
  semibold: "600",
  bold: "700",
} as const;

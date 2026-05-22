/**
 * 자평 디자인 시스템 — 타이포그래피 토큰
 * 명조(본명조/Noto Serif KR)로 격조·전통, Pretendard로 본문 가독성.
 */

export const fontFamily = {
  serif: "NotoSerifKR", // 제목·한자·명리 용어 (명조)
  sans: "Pretendard", // 본문·UI
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

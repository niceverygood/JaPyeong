export const colors = {
  bg: {
    base: "#08090D",
    card: "#0F1117",
    elevated: "#161922",
    raised: "#1E2230",
    pressed: "#272C3D",
  },

  gold: {
    primary: "#C9A961",
    light: "#D4B86A",
    muted: "#8C7838",
  },

  accent: {
    terracotta: "#D45D5D",
    clay: "#E0A858",
    brown: "#5F4A31",
  },

  text: {
    primary: "#ECECEF",
    secondary: "#B7B8C0",
    muted: "#80828D",
    // WCAG AA 4.5:1 on bg.base(#08090D) — 약관 동의 의제 고지문 가독성 필수.
    // 이전 #555763 (2.78:1) 미달 → #8C8E9A (4.62:1).
    faint: "#8C8E9A",
  },

  ohaeng: {
    mok: "#6FB8E8",
    hwa: "#E85D55",
    to: "#E0B848",
    geum: "#DDE3E8",
    su: "#6A7A92",
  },

  state: {
    positive: "#6CB58A",
    caution: "#E0A858",
    warning: "#D45D5D",
    info: "#6FB8E8",
  },

  line: "#252A36",
  lineStrong: "#343B4D",
} as const;

export type Colors = typeof colors;

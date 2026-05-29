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
    faint: "#555763",
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

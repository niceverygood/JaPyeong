/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./App.tsx", "./src/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        bg: {
          base: "#08090D",
          card: "#0F1117",
          elevated: "#161922",
          raised: "#1E2230",
          pressed: "#272C3D",
        },
        gold: {
          DEFAULT: "#C9A961",
          light: "#D4B86A",
          muted: "#8C7838",
        },
        accent: {
          terracotta: "#D45D5D",
          clay: "#E0A858",
          brown: "#5F4A31",
        },
        ink: {
          DEFAULT: "#ECECEF",
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
        line: "#252A36",
        lineStrong: "#343B4D",
      },
      fontFamily: {
        // 명조: 한국식 한자 자형(Noto Serif KR) → 한자가 자연스럽게 렌더됨
        serif: [
          '"Noto Serif KR"',
          '"Apple SD Gothic Neo"',
          '"Nanum Myeongjo"',
          "Batang",
          "serif",
        ],
        // 본문/UI: Pretendard Variable (한자는 Noto Serif KR로 fallback)
        sans: [
          '"Pretendard Variable"',
          "Pretendard",
          '"Apple SD Gothic Neo"',
          '"Malgun Gothic"',
          "system-ui",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

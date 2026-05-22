/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./App.tsx", "./src/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        bg: {
          base: "#0F1419",
          elevated: "#1A2129",
          card: "#2A251F",
        },
        gold: {
          DEFAULT: "#C9A961",
          light: "#D4B574",
          muted: "#8B7A4D",
        },
        accent: {
          terracotta: "#C96442",
          clay: "#C97B5A",
          brown: "#8B5A3C",
        },
        ink: {
          DEFAULT: "#F5EFE0",
          secondary: "#B8B0A0",
          muted: "#6B6357",
        },
        ohaeng: {
          mok: "#7A9B6E",
          hwa: "#A04545",
          to: "#8B7A4D",
          geum: "#D4B574",
          su: "#4A6FA5",
        },
        line: "#2E3640",
      },
      fontFamily: {
        serif: ["NotoSerifKR"],
        sans: ["Pretendard"],
      },
    },
  },
  plugins: [],
};

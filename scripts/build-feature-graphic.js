/**
 * Google Play Feature Graphic 생성 — 1024×500 PNG.
 *
 * Play Store 앱 등록 시 필수. 검색 결과·앱 상세 페이지 상단 배너로 노출됨.
 *
 * 출력: mobile/assets/store-screenshots/play-feature-graphic.png
 *
 * 실행: NODE_PATH=/Users/seungsoohan/.npm-global/lib/node_modules \
 *         node scripts/build-feature-graphic.js
 */

const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const OUT_DIR = path.resolve(__dirname, "..", "mobile", "assets", "store-screenshots");
const OUT = path.join(OUT_DIR, "play-feature-graphic.png");

const W = 1024, H = 500;
const C = {
  bg: "#0E0F13",
  surface: "#15171E",
  gold: "#C9A961",
  goldDim: "#8C7838",
  goldLight: "#D4B86A",
  text: "#ECECEF",
  text2: "#B7B8C0",
  textMut: "#80828D",
  line: "#2A2E3A",
};
const F_SERIF = "'PingFang SC', 'Noto Serif KR', 'Apple SD Gothic Neo', 'Nanum Myeongjo', serif";
const F_SANS = "-apple-system, 'Apple SD Gothic Neo', 'Helvetica Neue', sans-serif";

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs>
    <linearGradient id="bgg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#13151A"/>
      <stop offset="60%" stop-color="#0A0B0F"/>
      <stop offset="100%" stop-color="#08090D"/>
    </linearGradient>
    <radialGradient id="goldGlow" cx="0.75" cy="0.5" r="0.5">
      <stop offset="0%" stop-color="${C.gold}" stop-opacity="0.18"/>
      <stop offset="60%" stop-color="${C.gold}" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="${C.gold}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <!-- 배경 -->
  <rect width="${W}" height="${H}" fill="url(#bgg)"/>
  <rect width="${W}" height="${H}" fill="url(#goldGlow)"/>

  <!-- 좌측: 子平 큰 워드마크 + 슬로건 -->
  <g transform="translate(56, 0)">
    <!-- 子平 -->
    <text x="0" y="220"
          font-family="${F_SERIF}"
          font-size="180" font-weight="900" fill="${C.text}">子</text>
    <text x="160" y="220"
          font-family="${F_SERIF}"
          font-size="180" font-weight="900" fill="${C.gold}">平</text>

    <!-- 골드 라인 -->
    <line x1="0" y1="248" x2="160" y2="248"
          stroke="${C.gold}" stroke-width="3"/>

    <!-- 자평 / JAPYEONG -->
    <text x="0" y="290"
          font-family="${F_SANS}"
          font-size="20" fill="${C.text2}"
          letter-spacing="6">자 평  ·  J A P Y E O N G</text>

    <!-- 슬로건 -->
    <text x="0" y="370"
          font-family="${F_SERIF}"
          font-size="44" font-weight="900" fill="${C.text}">결정 앞에, 자평.</text>

    <!-- 서브 -->
    <text x="0" y="410"
          font-family="${F_SANS}"
          font-size="22" fill="${C.text2}">AI 보조 고전 해석 + 자문위원 1:1</text>
  </g>

  <!-- 우측: 미니 앱 화면 mock -->
  <g transform="translate(600, 50)">
    <!-- 외곽 폰 프레임 -->
    <rect x="0" y="0" width="360" height="400" rx="40" ry="40"
          fill="${C.surface}" stroke="${C.goldDim}" stroke-width="2"/>

    <!-- 상단 status bar -->
    <rect x="0" y="0" width="360" height="34" rx="40" ry="40" fill="${C.bg}"/>

    <!-- 사주판 미니 (4기둥) -->
    <g transform="translate(28, 60)">
      <text x="0" y="22"
            font-family="${F_SERIF}" font-size="14" fill="${C.gold}"
            letter-spacing="2" font-weight="700">本 · 명식 분석</text>

      <!-- 4 기둥 -->
      ${["乙丑", "丁亥", "丁巳", "丁未"].map((p, i) => {
        const isDay = i === 2;
        return `
          <g transform="translate(${i * 76}, 50)">
            <rect width="68" height="100" rx="8"
                  fill="${isDay ? "rgba(201,169,97,0.10)" : C.bg}"
                  stroke="${isDay ? C.gold : C.line}"
                  stroke-width="${isDay ? 2 : 1}"/>
            <text x="34" y="46"
                  font-family="${F_SERIF}" font-size="32"
                  fill="${C.gold}" font-weight="900"
                  text-anchor="middle">${p[0]}</text>
            <text x="34" y="82"
                  font-family="${F_SERIF}" font-size="28"
                  fill="${C.text}" font-weight="700"
                  text-anchor="middle">${p[1]}</text>
          </g>
        `;
      }).join("")}
    </g>

    <!-- 인생 흐름 미니 그래프 -->
    <g transform="translate(28, 240)">
      <text x="0" y="0"
            font-family="${F_SERIF}" font-size="14" fill="${C.gold}"
            letter-spacing="2" font-weight="700">流 · 인생 흐름</text>

      <rect x="0" y="14" width="304" height="60" rx="6"
            fill="${C.bg}" stroke="${C.line}"/>
      <line x1="0" y1="44" x2="304" y2="44" stroke="${C.line}"/>

      ${[-1.5, +0.5, +2.5, +3.0, +1.0, -1.0, -2.5, +0.5, +1.5].map((s, i) => {
        const x = 18 + i * 32;
        const half = 26;
        const ratio = Math.min(Math.abs(s) / 5, 1);
        const barH = ratio * half;
        const y = s >= 0 ? 44 - barH : 44;
        const color = s >= 1.5 ? C.gold : s <= -1.5 ? "#E85D55" : C.textMut;
        return `<rect x="${x}" y="${y}" width="16" height="${barH}"
                rx="2" fill="${color}" opacity="${i === 3 ? 1 : 0.8}"/>`;
      }).join("")}

      <text x="152" y="100"
            font-family="${F_SANS}" font-size="12" fill="${C.textMut}"
            text-anchor="middle">대운 80년 길흉 시각화</text>
    </g>
  </g>

  <!-- 우측 상단 라벨 — 마케팅 -->
  <g transform="translate(${W - 220}, 38)">
    <rect width="170" height="32" rx="16"
          fill="${C.bg}" stroke="${C.gold}" stroke-width="1.5"/>
    <text x="85" y="22"
          font-family="${F_SERIF}" font-size="13" fill="${C.gold}"
          letter-spacing="3" font-weight="700"
          text-anchor="middle">明 · 명리 자문 도구</text>
  </g>
</svg>`;

(async () => {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  await sharp(Buffer.from(svg))
    .resize(W, H)
    .png({ quality: 100, compressionLevel: 9 })
    .toFile(OUT);
  console.log(`✓ ${path.relative(process.cwd(), OUT)}  ${W}×${H}`);
})().catch(e => { console.error(e); process.exit(1); });

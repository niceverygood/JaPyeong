/**
 * 자평 앱 아이콘 + 스플래시 + 어댑티브 아이콘 생성.
 *
 * 출력:
 *  - mobile/assets/icon.png           1024x1024  (iOS App Store, Expo 메인)
 *  - mobile/assets/adaptive-icon.png  1024x1024  (Android adaptive, 포어그라운드)
 *  - mobile/assets/splash.png         1284x2778  (스플래시, 9:19.5)
 *  - mobile/assets/favicon.png         48x48     (웹 favicon)
 *
 * 디자인: 子平 워드마크 — 다크 #0E0F13 배경 + 子(흰) 平(골드 #C9A961)
 * 폰트는 SVG에서 시스템 serif 사용 (sharp는 폰트 임베딩 못함 — 디자인 단순함)
 *
 * 실행: NODE_PATH=/Users/seungsoohan/.npm-global/lib/node_modules node scripts/build-app-assets.js
 */

const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const OUT_DIR = path.resolve(__dirname, "..", "mobile", "assets");

const BG = "#0E0F13";
const GOLD = "#C9A961";
const WHITE = "#ECECEF";

// ── 헬퍼: SVG → PNG ─────────────────────────────────────────
async function svgToPng(svg, w, h, outPath) {
  await sharp(Buffer.from(svg))
    .resize(w, h)
    .png({ quality: 100, compressionLevel: 9 })
    .toFile(outPath);
  console.log(`✓ ${path.relative(process.cwd(), outPath)}  ${w}×${h}`);
}

// ── 메인 아이콘 (1024x1024) ─────────────────────────────────
// iOS App Store, Expo 기본 아이콘
// 가운데 子平 워드마크. 둘레 골드 얇은 링.
function makeIconSvg(size) {
  const cx = size / 2, cy = size / 2;
  const fontSize = size * 0.42;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#13151A"/>
        <stop offset="100%" stop-color="#08090D"/>
      </linearGradient>
    </defs>
    <rect width="${size}" height="${size}" fill="url(#bg)"/>
    <!-- 외곽 골드 링 -->
    <rect x="${size*0.04}" y="${size*0.04}" width="${size*0.92}" height="${size*0.92}"
          rx="${size*0.18}" ry="${size*0.18}"
          fill="none" stroke="${GOLD}" stroke-opacity="0.35" stroke-width="${size*0.005}"/>
    <!-- 子 (흰) -->
    <text x="${cx - fontSize * 0.55}" y="${cy + fontSize * 0.35}"
          font-family="'PingFang SC', 'Noto Serif KR', 'Apple SD Gothic Neo', 'Noto Serif TC', serif"
          font-size="${fontSize}" font-weight="900"
          fill="${WHITE}" text-anchor="middle">子</text>
    <!-- 平 (골드) -->
    <text x="${cx + fontSize * 0.55}" y="${cy + fontSize * 0.35}"
          font-family="'PingFang SC', 'Noto Serif KR', 'Apple SD Gothic Neo', 'Noto Serif TC', serif"
          font-size="${fontSize}" font-weight="900"
          fill="${GOLD}" text-anchor="middle">平</text>
    <!-- 하단 영문 -->
    <text x="${cx}" y="${size - size*0.085}"
          font-family="-apple-system, 'Helvetica Neue', sans-serif"
          font-size="${size*0.052}" font-weight="500"
          letter-spacing="${size*0.012}"
          fill="${GOLD}" fill-opacity="0.55"
          text-anchor="middle">JAPYEONG</text>
  </svg>`;
}

// ── Android adaptive (1024x1024 foreground only, safe zone 안에 시각요소) ─────
// adaptive 아이콘은 가운데 66% 원 안에 시각 핵심이 들어가야 마스크 깨짐 없음.
function makeAdaptiveSvg(size) {
  const cx = size / 2, cy = size / 2;
  const fontSize = size * 0.32;  // adaptive는 더 작게 (safe zone)
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <rect width="${size}" height="${size}" fill="${BG}"/>
    <text x="${cx - fontSize * 0.55}" y="${cy + fontSize * 0.35}"
          font-family="'PingFang SC', 'Noto Serif KR', serif"
          font-size="${fontSize}" font-weight="900"
          fill="${WHITE}" text-anchor="middle">子</text>
    <text x="${cx + fontSize * 0.55}" y="${cy + fontSize * 0.35}"
          font-family="'PingFang SC', 'Noto Serif KR', serif"
          font-size="${fontSize}" font-weight="900"
          fill="${GOLD}" text-anchor="middle">平</text>
  </svg>`;
}

// ── 스플래시 (1284x2778, iPhone 14 Pro Max 비율) ────────────
// resizeMode: contain 일 때 가운데 자동 정렬. 배경 단색.
function makeSplashSvg(w, h) {
  const cx = w / 2, cy = h / 2;
  const fontSize = w * 0.18;
  const subY = cy + fontSize * 0.9;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <rect width="${w}" height="${h}" fill="${BG}"/>
    <text x="${cx - fontSize * 0.55}" y="${cy + fontSize * 0.35}"
          font-family="'PingFang SC', 'Noto Serif KR', 'Apple SD Gothic Neo', serif"
          font-size="${fontSize}" font-weight="900"
          fill="${WHITE}" text-anchor="middle">子</text>
    <text x="${cx + fontSize * 0.55}" y="${cy + fontSize * 0.35}"
          font-family="'PingFang SC', 'Noto Serif KR', serif"
          font-size="${fontSize}" font-weight="900"
          fill="${GOLD}" text-anchor="middle">平</text>
    <!-- 가운데 골드 라인 -->
    <line x1="${cx - 40}" y1="${subY + 30}" x2="${cx + 40}" y2="${subY + 30}"
          stroke="${GOLD}" stroke-width="2" stroke-opacity="0.6"/>
    <text x="${cx}" y="${subY + 80}"
          font-family="-apple-system, sans-serif"
          font-size="${w*0.028}" font-weight="500"
          letter-spacing="${w*0.014}"
          fill="${GOLD}" fill-opacity="0.7"
          text-anchor="middle">결정 앞에, 자평.</text>
  </svg>`;
}

// ── favicon (48x48 — 텍스트 너무 작아 단순 골드 平 한 글자만) ─
function makeFaviconSvg(size) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <rect width="${size}" height="${size}" rx="${size*0.18}" fill="${BG}"/>
    <text x="${size/2}" y="${size*0.76}"
          font-family="'PingFang SC', 'Noto Serif KR', serif"
          font-size="${size*0.78}" font-weight="900"
          fill="${GOLD}" text-anchor="middle">平</text>
  </svg>`;
}

(async () => {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  await svgToPng(makeIconSvg(1024), 1024, 1024, path.join(OUT_DIR, "icon.png"));
  await svgToPng(makeAdaptiveSvg(1024), 1024, 1024, path.join(OUT_DIR, "adaptive-icon.png"));
  await svgToPng(makeSplashSvg(1284, 2778), 1284, 2778, path.join(OUT_DIR, "splash.png"));
  await svgToPng(makeFaviconSvg(48), 48, 48, path.join(OUT_DIR, "favicon.png"));
  console.log("\n✅ 4 assets generated.");
})().catch(e => { console.error(e); process.exit(1); });

/**
 * 자평 앱스토어 스크린샷 자동 생성.
 *
 * 출력 (12장):
 *   mobile/assets/store-screenshots/
 *     ios-1-hero.png            1290×2796  (iPhone 14 Pro Max)
 *     ios-2-saju.png            1290×2796
 *     ios-3-life-flow.png       1290×2796
 *     ios-4-ai-consult.png      1290×2796
 *     ios-5-compatibility.png   1290×2796
 *     ios-6-decision.png        1290×2796
 *     android-1-hero.png        1080×1920  (Play Store phone)
 *     android-2-saju.png        1080×1920
 *     ...
 *
 * 디자인: 자평 디자인 토큰 (다크 #0E0F13 + 골드 #C9A961)
 *   - 상단 18% : 한국어 명조 헤드라인 (마케팅 카피)
 *   - 중간 8%  : 산스 서브카피
 *   - 본문 64% : 앱 화면 mock (실 화면 미러링)
 *   - 하단 10% : 子平 워드마크 + tagline
 *
 * 실행:
 *   NODE_PATH=/Users/seungsoohan/.npm-global/lib/node_modules \
 *     node scripts/build-store-screenshots.js
 */

const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const OUT_DIR = path.resolve(__dirname, "..", "mobile", "assets", "store-screenshots");

const C = {
  bg: "#0E0F13",
  surface: "#15171E",
  surface2: "#1B1E27",
  card: "#0F1117",
  gold: "#C9A961",
  goldDim: "#8C7838",
  goldLight: "#D4B86A",
  text: "#ECECEF",
  text2: "#B7B8C0",
  textMut: "#80828D",
  line: "#2A2E3A",
  lineStrong: "#3A3F4F",
  ok: "#6CB58A",
  warn: "#E0A858",
  bad: "#D45D5D",
  hwa: "#E85D55",
  mok: "#6FB8E8",
  to: "#E0B848",
};

// 시스템 폰트 (Mac에서 한자·한글 양호하게 렌더)
const F_SERIF = "'PingFang SC', 'Noto Serif KR', 'Apple SD Gothic Neo', 'Nanum Myeongjo', serif";
const F_SANS = "-apple-system, 'Apple SD Gothic Neo', 'Helvetica Neue', sans-serif";

// ── 공통 헬퍼 ─────────────────────────────────────────────
function header(W, H, eyebrow, headline, sub) {
  // 헤드라인 크기 자동 조정 (글자수 따라)
  const headlineSize = headline.length > 18 ? W * 0.062 : W * 0.078;
  const eyebrowY = H * 0.045;
  const headlineY = H * 0.085;
  const subY = H * 0.155;
  return `
    <text x="${W/2}" y="${eyebrowY}"
          font-family="${F_SERIF}"
          font-size="${W*0.024}" fill="${C.gold}"
          letter-spacing="${W*0.008}"
          text-anchor="middle" font-weight="700">${eyebrow}</text>

    <text x="${W/2}" y="${headlineY}"
          font-family="${F_SERIF}"
          font-size="${headlineSize}" fill="${C.text}"
          text-anchor="middle" font-weight="900">${headline}</text>

    <text x="${W/2}" y="${subY}"
          font-family="${F_SANS}"
          font-size="${W*0.036}" fill="${C.text2}"
          text-anchor="middle" font-weight="500"
          letter-spacing="${W*0.002}">${sub}</text>
  `;
}

function footer(W, H) {
  const y = H * 0.95;
  return `
    <text x="${W*0.5 - W*0.04}" y="${y}"
          font-family="${F_SERIF}"
          font-size="${W*0.05}" fill="${C.text}"
          text-anchor="middle" font-weight="900">子</text>
    <text x="${W*0.5 + W*0.04}" y="${y}"
          font-family="${F_SERIF}"
          font-size="${W*0.05}" fill="${C.gold}"
          text-anchor="middle" font-weight="900">平</text>
    <text x="${W/2}" y="${y + W*0.035}"
          font-family="${F_SANS}"
          font-size="${W*0.022}" fill="${C.textMut}"
          text-anchor="middle" letter-spacing="${W*0.012}">JAPYEONG</text>
  `;
}

function frame(W, H, contentY, contentH) {
  // 앱 화면 mock 컨테이너 — 약간 안쪽으로 (iPhone 채널 느낌)
  const padX = W * 0.06;
  return `
    <!-- 화면 외곽 다크 -->
    <rect x="${padX}" y="${contentY}" width="${W - padX*2}" height="${contentH}"
          rx="${W*0.04}" ry="${W*0.04}"
          fill="${C.bg}" stroke="${C.lineStrong}" stroke-width="2"/>
  `;
}

// ── 스크린샷 1 · HERO ─────────────────────────────────────
function screenHero(W, H) {
  const contentY = H * 0.20;
  const contentH = H * 0.66;
  const cx = W / 2;
  const cy = contentY + contentH / 2;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <defs>
      <linearGradient id="bgg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#13151A"/>
        <stop offset="100%" stop-color="#08090D"/>
      </linearGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#bgg)"/>

    ${header(W, H, "禮 · ANNUAL 2026", "결정 앞에, 자평.", "AI 보조 고전 해석 + 자문위원 1:1")}
    ${frame(W, H, contentY, contentH)}

    <!-- 메인 한자 워드마크 (중앙) -->
    <text x="${cx - W*0.14}" y="${cy - H*0.04}"
          font-family="${F_SERIF}"
          font-size="${W*0.36}" fill="${C.text}"
          text-anchor="middle" font-weight="900">子</text>
    <text x="${cx + W*0.14}" y="${cy - H*0.04}"
          font-family="${F_SERIF}"
          font-size="${W*0.36}" fill="${C.gold}"
          text-anchor="middle" font-weight="900">平</text>

    <!-- 골드 라인 -->
    <line x1="${cx - W*0.08}" y1="${cy + H*0.05}" x2="${cx + W*0.08}" y2="${cy + H*0.05}"
          stroke="${C.gold}" stroke-width="2"/>

    <!-- 미니 사주판 미리보기 (4기둥) -->
    <g transform="translate(${cx - W*0.35}, ${cy + H*0.09})">
      ${["丁 巳", "丁 未", "丁 巳", "乙 丑"].map((p, i) => `
        <g transform="translate(${i * W*0.175}, 0)">
          <rect width="${W*0.155}" height="${W*0.21}"
                rx="${W*0.012}" fill="${C.surface}" stroke="${C.line}" stroke-width="1"/>
          <text x="${W*0.0775}" y="${W*0.085}"
                font-family="${F_SERIF}" font-size="${W*0.065}"
                fill="${i === 2 ? C.gold : C.text}" font-weight="900"
                text-anchor="middle">${p.split(" ")[0]}</text>
          <text x="${W*0.0775}" y="${W*0.165}"
                font-family="${F_SERIF}" font-size="${W*0.06}"
                fill="${C.text2}" font-weight="700"
                text-anchor="middle">${p.split(" ")[1]}</text>
        </g>
      `).join("")}
    </g>

    <!-- 본문 하단 한줄 -->
    <text x="${cx}" y="${contentY + contentH - W*0.05}"
          font-family="${F_SERIF}"
          font-size="${W*0.026}" fill="${C.textMut}"
          text-anchor="middle">900년 명리학 고전 위에서, AI와 사람이 함께</text>

    ${footer(W, H)}
  </svg>`;
}

// ── 스크린샷 2 · 사주 명식 분석 ────────────────────────────
function screenSaju(W, H) {
  const contentY = H * 0.20;
  const contentH = H * 0.66;
  const padX = W * 0.10;
  const innerW = W - padX * 2;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${C.bg}"/>

    ${header(W, H, "本 · 명식 분석", "사주 8자를 코드가 확정", "절기·진태양시·60갑자 자동 산출")}
    ${frame(W, H, contentY, contentH)}

    <!-- 사주판 큰 카드 -->
    <g transform="translate(${padX + W*0.02}, ${contentY + H*0.04})">
      <!-- 헤더 -->
      <text x="${innerW*0.5 - W*0.02 - W*0.02 - W*0.005}" y="${W*0.04}"
            font-family="${F_SERIF}" font-size="${W*0.04}" fill="${C.gold}"
            font-weight="900" letter-spacing="${W*0.005}" text-anchor="end">RULED · 결정론 엔진</text>

      <!-- 4 기둥 -->
      ${["年柱 乙丑", "月柱 丁亥", "日柱 丁巳", "時柱 丁未"].map((p, i) => {
        const [label, pillar] = p.split(" ");
        const isDay = i === 2;
        const x = i * (innerW * 0.235 + W*0.015);
        return `
          <g transform="translate(${x}, ${W*0.075})">
            <rect width="${innerW*0.235}" height="${H*0.20}"
                  rx="${W*0.015}"
                  fill="${isDay ? "rgba(201,169,97,0.10)" : C.surface}"
                  stroke="${isDay ? C.gold : C.line}" stroke-width="${isDay ? 2 : 1}"/>
            <text x="${innerW*0.235*0.5}" y="${W*0.035}"
                  font-family="${F_SANS}" font-size="${W*0.022}"
                  fill="${C.textMut}" text-anchor="middle">${label}</text>
            <text x="${innerW*0.235*0.5}" y="${W*0.13}"
                  font-family="${F_SERIF}" font-size="${W*0.10}"
                  fill="${C.gold}" font-weight="900"
                  text-anchor="middle">${pillar[0]}</text>
            <text x="${innerW*0.235*0.5}" y="${W*0.22}"
                  font-family="${F_SERIF}" font-size="${W*0.085}"
                  fill="${C.text}" font-weight="700"
                  text-anchor="middle">${pillar[1]}</text>
          </g>
        `;
      }).join("")}

      <!-- 일간 + 오행 + 균형 -->
      <g transform="translate(0, ${H*0.30})">
        ${[
          { label: "일간", value: "丁火", color: C.gold },
          { label: "오행", value: "火 5", color: C.hwa },
          { label: "균형", value: "62%", color: C.mok },
        ].map((item, i) => `
          <g transform="translate(${i * (innerW * 0.32 + W*0.01)}, 0)">
            <rect width="${innerW*0.32}" height="${H*0.07}"
                  rx="${W*0.012}" fill="${C.surface}" stroke="${C.line}"/>
            <text x="${W*0.025}" y="${H*0.027}"
                  font-family="${F_SANS}" font-size="${W*0.025}" fill="${C.textMut}">${item.label}</text>
            <text x="${W*0.025}" y="${H*0.057}"
                  font-family="${F_SERIF}" font-size="${W*0.05}" font-weight="900"
                  fill="${item.color}">${item.value}</text>
          </g>
        `).join("")}
      </g>

      <!-- 십성 분포 -->
      <g transform="translate(0, ${H*0.40})">
        <text x="0" y="${W*0.035}"
              font-family="${F_SERIF}" font-size="${W*0.032}" fill="${C.gold}"
              font-weight="700" letter-spacing="${W*0.006}">十星 · 십성 분포</text>
        ${[
          { label: "비견", n: 3 }, { label: "겁재", n: 1 },
          { label: "식신", n: 2 }, { label: "상관", n: 0 },
          { label: "정재", n: 1 }, { label: "편재", n: 2 },
        ].map((g, i) => `
          <g transform="translate(${(i%3) * (innerW * 0.33 + W*0.008)}, ${W*0.07 + Math.floor(i/3) * W*0.10})">
            <rect width="${innerW*0.32}" height="${W*0.085}"
                  rx="${W*0.01}" fill="${C.surface2}" stroke="${C.line}" stroke-width="0.5"/>
            <text x="${W*0.02}" y="${W*0.05}"
                  font-family="${F_SERIF}" font-size="${W*0.034}" fill="${C.text}">${g.label}</text>
            <text x="${innerW*0.32 - W*0.02}" y="${W*0.055}"
                  font-family="${F_SERIF}" font-size="${W*0.04}" fill="${C.gold}"
                  font-weight="900" text-anchor="end">${g.n}</text>
          </g>
        `).join("")}
      </g>
    </g>

    ${footer(W, H)}
  </svg>`;
}

// ── 스크린샷 3 · 인생 흐름 그래프 ───────────────────────────
function screenLifeFlow(W, H) {
  const contentY = H * 0.20;
  const contentH = H * 0.66;
  const padX = W * 0.10;
  const innerW = W - padX * 2;

  // 9개 막대 점수 (예시)
  const bars = [-1.5, +0.5, +2.5, +3.0, +1.0, -1.0, -2.5, +0.5, +1.5];
  const labels = ["10", "20", "30", "40", "50", "60", "70", "80", "90"];

  const graphY = contentY + H * 0.06;
  const graphH = H * 0.32;
  const barAreaH = graphH;
  const baseline = graphY + graphH / 2;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${C.bg}"/>

    ${header(W, H, "流 · 인생 흐름", "대운 80년을 한 화면에", "용신·기신으로 길흉 시각화")}
    ${frame(W, H, contentY, contentH)}

    <!-- 그래프 영역 배경 -->
    <rect x="${padX + W*0.02}" y="${graphY}" width="${innerW - W*0.04}" height="${graphH}"
          rx="${W*0.015}" fill="${C.card}" stroke="${C.line}"/>

    <!-- baseline -->
    <line x1="${padX + W*0.02}" y1="${baseline}" x2="${padX + innerW - W*0.02}" y2="${baseline}"
          stroke="${C.line}" stroke-width="1"/>

    <!-- 막대 -->
    ${bars.map((score, i) => {
      const x = padX + W*0.03 + i * ((innerW - W*0.06) / 9);
      const barW = (innerW - W*0.06) / 9 - W*0.012;
      const half = barAreaH / 2 - 8;
      const ratio = Math.min(Math.abs(score) / 5, 1);
      const barH = ratio * half;
      const y = score >= 0 ? baseline - barH : baseline;
      const color = score >= 1.5 ? C.gold : score <= -1.5 ? C.hwa : C.textMut;
      const isPeak = i === 3;
      return `
        <rect x="${x + barW*0.15}" y="${y}" width="${barW * 0.7}" height="${barH}"
              rx="${W*0.005}" fill="${color}" opacity="${isPeak ? 1 : 0.75}"/>
        ${isPeak ? `<circle cx="${x + barW*0.5}" cy="${y - W*0.015}" r="${W*0.012}" fill="${C.gold}"/>` : ""}
      `;
    }).join("")}

    <!-- 가로축 라벨 -->
    ${labels.map((age, i) => {
      const x = padX + W*0.03 + i * ((innerW - W*0.06) / 9) + ((innerW - W*0.06) / 9 - W*0.012) * 0.5;
      const isPeak = i === 3;
      const ganji = ["丁", "戊", "己", "庚", "辛", "壬", "癸", "甲", "乙"][i];
      const ji = ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"][i];
      return `
        <text x="${x}" y="${graphY + graphH + W*0.04}"
              font-family="${F_SANS}" font-size="${W*0.022}"
              fill="${isPeak ? C.gold : C.textMut}"
              text-anchor="middle">${age}</text>
        <text x="${x}" y="${graphY + graphH + W*0.075}"
              font-family="${F_SERIF}" font-size="${W*0.028}"
              fill="${C.goldLight}"
              text-anchor="middle">${ganji}${ji}</text>
        <text x="${x}" y="${graphY + graphH + W*0.105}"
              font-family="${F_SANS}" font-size="${W*0.02}"
              fill="${bars[i] >= 1.5 ? C.gold : bars[i] <= -1.5 ? C.hwa : C.textMut}"
              text-anchor="middle">${bars[i] >= 3 ? "대길" : bars[i] >= 1.5 ? "길" : bars[i] >= -1.5 ? "평" : bars[i] >= -3 ? "주의" : "흉"}</text>
      `;
    }).join("")}

    <!-- 선택된 주기 사유 카드 -->
    <g transform="translate(${padX + W*0.02}, ${graphY + graphH + W*0.16})">
      <rect width="${innerW - W*0.04}" height="${H*0.16}"
            rx="${W*0.015}" fill="${C.surface}" stroke="${C.line}"/>
      <text x="${W*0.025}" y="${W*0.05}"
            font-family="${F_SERIF}" font-size="${W*0.035}" fill="${C.text}"
            font-weight="700">40~49세 · 庚寅 · 대길 (+3.0)</text>
      <text x="${W*0.025}" y="${W*0.10}"
            font-family="${F_SANS}" font-size="${W*0.027}" fill="${C.text2}">· 대운 천간 庚(金) = 용신</text>
      <text x="${W*0.025}" y="${W*0.135}"
            font-family="${F_SANS}" font-size="${W*0.027}" fill="${C.text2}">· 일지 巳와 寅 육합</text>
      <text x="${W*0.025}" y="${W*0.17}"
            font-family="${F_SANS}" font-size="${W*0.027}" fill="${C.text2}">· 인생 큰 흐름의 전환점 — 관성 강화</text>
    </g>

    ${footer(W, H)}
  </svg>`;
}

// ── 스크린샷 4 · AI 자문 (12 카테고리) ─────────────────────
function screenAiConsult(W, H) {
  const contentY = H * 0.20;
  const contentH = H * 0.66;
  const padX = W * 0.10;
  const innerW = W - padX * 2;

  const categories = [
    { h: "職", l: "진로" }, { h: "業", l: "사업" }, { h: "財", l: "재정" },
    { h: "緣", l: "연애" }, { h: "婚", l: "결혼" }, { h: "子", l: "자녀" },
    { h: "家", l: "가족" }, { h: "體", l: "건강" }, { h: "學", l: "학업" },
    { h: "移", l: "이주" }, { h: "心", l: "마음" }, { h: "變", l: "전환" },
  ];

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${C.bg}"/>

    ${header(W, H, "問 · AI 자문", "12 카테고리 즉시 풀이", "직업·결혼·자녀·재정 등")}
    ${frame(W, H, contentY, contentH)}

    <!-- 4×3 카테고리 그리드 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.04})">
      ${categories.map((c, i) => {
        const col = i % 4, row = Math.floor(i / 4);
        const cw = (innerW - W*0.05) / 4 - W*0.012;
        const ch = H * 0.085;
        const x = col * (cw + W*0.012);
        const y = row * (ch + W*0.015);
        const isActive = c.h === "緣";
        return `
          <g transform="translate(${x}, ${y})">
            <rect width="${cw}" height="${ch}"
                  rx="${W*0.014}"
                  fill="${isActive ? "rgba(201,169,97,0.10)" : C.surface}"
                  stroke="${isActive ? C.gold : C.line}"
                  stroke-width="${isActive ? 2 : 1}"/>
            <text x="${cw/2 - W*0.025}" y="${ch * 0.62}"
                  font-family="${F_SERIF}" font-size="${W*0.052}"
                  fill="${isActive ? C.gold : C.goldLight}"
                  font-weight="900" text-anchor="middle">${c.h}</text>
            <text x="${cw/2 + W*0.025}" y="${ch * 0.62}"
                  font-family="${F_SANS}" font-size="${W*0.028}"
                  fill="${isActive ? C.text : C.text2}"
                  text-anchor="middle">${c.l}</text>
          </g>
        `;
      }).join("")}
    </g>

    <!-- 결과 미리보기 카드 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.32})">
      <rect width="${innerW - W*0.05}" height="${H*0.30}"
            rx="${W*0.018}" fill="${C.surface2}" stroke="${C.gold}" stroke-width="1.5"/>

      <!-- 헤더 -->
      <text x="${W*0.025}" y="${W*0.04}"
            font-family="${F_SERIF}" font-size="${W*0.032}" fill="${C.gold}"
            font-weight="700" letter-spacing="${W*0.005}">緣 · 연애·인연 풀이</text>

      <text x="${innerW - W*0.075}" y="${W*0.04}"
            font-family="${F_SANS}" font-size="${W*0.022}" fill="${C.text2}"
            text-anchor="end">신뢰도 medium</text>

      <line x1="${W*0.025}" y1="${W*0.055}" x2="${innerW - W*0.075}" y2="${W*0.055}"
            stroke="${C.line}" stroke-width="0.5"/>

      <!-- 본문 (3줄) -->
      <text x="${W*0.025}" y="${W*0.105}"
            font-family="${F_SANS}" font-size="${W*0.026}" fill="${C.text}">
        丁火(정화) 일간에 壬水(정관)와 甲木(편인)이</text>
      <text x="${W*0.025}" y="${W*0.14}"
            font-family="${F_SANS}" font-size="${W*0.026}" fill="${C.text}">
        교차합니다. 인연의 결은 우선 흐릿하지만</text>
      <text x="${W*0.025}" y="${W*0.175}"
            font-family="${F_SANS}" font-size="${W*0.026}" fill="${C.text}">
        甲申(갑신)대운 이후 정리될 가능성이 있습니다.</text>

      <!-- 학파 견해 -->
      <g transform="translate(${W*0.025}, ${W*0.22})">
        <rect width="${innerW - W*0.10}" height="${W*0.075}"
              rx="${W*0.008}" fill="${C.bg}" stroke="${C.goldDim}" stroke-width="0.5"/>
        <text x="${W*0.015}" y="${W*0.025}"
              font-family="${F_SERIF}" font-size="${W*0.022}" fill="${C.textMut}"
              letter-spacing="${W*0.005}">학파별 견해</text>
        <text x="${W*0.015}" y="${W*0.055}"
              font-family="${F_SANS}" font-size="${W*0.024}" fill="${C.text2}">
          ◦ 자평진전: 정관 우선. 적천수: 조후 우선.</text>
      </g>

      <!-- 인용 칩 -->
      <g transform="translate(${W*0.025}, ${W*0.32})">
        <rect width="${W*0.32}" height="${W*0.04}"
              rx="${W*0.008}" fill="${C.bg}" stroke="${C.goldDim}"/>
        <text x="${W*0.025}" y="${W*0.028}"
              font-family="${F_SERIF}" font-size="${W*0.022}" fill="${C.gold}">
          연해자평 권3 · 정관편</text>
      </g>
    </g>

    ${footer(W, H)}
  </svg>`;
}

// ── 스크린샷 5 · 궁합 ──────────────────────────────────────
function screenCompat(W, H) {
  const contentY = H * 0.20;
  const contentH = H * 0.66;
  const padX = W * 0.10;
  const innerW = W - padX * 2;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${C.bg}"/>

    ${header(W, H, "宮 · 궁합", "두 사주의 결을 함께", "학파별 견해 솔직히 표기")}
    ${frame(W, H, contentY, contentH)}

    <!-- 두 사주 카드 좌·우 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.04})">
      ${[
        { label: "나 (我)", gan: "丁", ji: "巳", note: "丁火 일간 · 정인" },
        { label: "상대 (彼)", gan: "壬", ji: "子", note: "壬水 일간 · 정관" }
      ].map((p, i) => `
        <g transform="translate(${i * (innerW * 0.51 + W*0.01)}, 0)">
          <rect width="${innerW*0.49}" height="${H*0.16}"
                rx="${W*0.018}" fill="${C.surface}" stroke="${C.line}"/>
          <text x="${W*0.025}" y="${W*0.04}"
                font-family="${F_SERIF}" font-size="${W*0.028}" fill="${C.gold}"
                font-weight="700" letter-spacing="${W*0.005}">${p.label}</text>
          <text x="${innerW*0.49 / 2 - W*0.05}" y="${W*0.14}"
                font-family="${F_SERIF}" font-size="${W*0.12}" fill="${C.text}"
                text-anchor="middle" font-weight="900">${p.gan}</text>
          <text x="${innerW*0.49 / 2 + W*0.05}" y="${W*0.14}"
                font-family="${F_SERIF}" font-size="${W*0.105}" fill="${C.gold}"
                text-anchor="middle" font-weight="700">${p.ji}</text>
          <text x="${innerW*0.49 / 2}" y="${H*0.16 - W*0.015}"
                font-family="${F_SANS}" font-size="${W*0.024}" fill="${C.text2}"
                text-anchor="middle">${p.note}</text>
        </g>
      `).join("")}
    </g>

    <!-- 결정론 신호 카드 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.22})">
      <rect width="${innerW*0.49}" height="${H*0.10}"
            rx="${W*0.014}" fill="${C.surface}" stroke="${C.line}"/>
      <text x="${W*0.02}" y="${W*0.038}"
            font-family="${F_SERIF}" font-size="${W*0.022}" fill="${C.gold}"
            letter-spacing="${W*0.005}">일간 관계</text>
      <text x="${W*0.02}" y="${W*0.085}"
            font-family="${F_SERIF}" font-size="${W*0.034}" fill="${C.text}"
            font-weight="700">丁 ↔ 壬 · 정관</text>
      <text x="${W*0.02}" y="${W*0.115}"
            font-family="${F_SANS}" font-size="${W*0.024}" fill="${C.text2}">
        B극A · 책임·규범 흐름</text>

      <g transform="translate(${innerW*0.51 + W*0.01}, 0)">
        <rect width="${innerW*0.49}" height="${H*0.10}"
              rx="${W*0.014}" fill="${C.surface}" stroke="${C.gold}" stroke-width="1.5"/>
        <text x="${W*0.02}" y="${W*0.038}"
              font-family="${F_SERIF}" font-size="${W*0.022}" fill="${C.gold}"
              letter-spacing="${W*0.005}">합 / 충</text>
        <text x="${W*0.02}" y="${W*0.085}"
              font-family="${F_SERIF}" font-size="${W*0.034}" fill="${C.text}"
              font-weight="700">합 2 · 충 1</text>
        <text x="${W*0.02}" y="${W*0.115}"
              font-family="${F_SANS}" font-size="${W*0.024}" fill="${C.gold}">
          오행 보완 +0.18 (보완 흐름)</text>
      </g>
    </g>

    <!-- 자문 결과 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.35})">
      <rect width="${innerW - W*0.05}" height="${H*0.26}"
            rx="${W*0.018}" fill="${C.surface2}" stroke="${C.line}"/>
      <text x="${W*0.025}" y="${W*0.042}"
            font-family="${F_SERIF}" font-size="${W*0.032}" fill="${C.gold}"
            font-weight="700" letter-spacing="${W*0.005}">궁합 풀이</text>

      <text x="${W*0.025}" y="${W*0.10}"
            font-family="${F_SANS}" font-size="${W*0.027}" fill="${C.text}">
        두 분의 일간은 정관 관계로 책임의 결이 흐릅니다.</text>
      <text x="${W*0.025}" y="${W*0.135}"
            font-family="${F_SANS}" font-size="${W*0.027}" fill="${C.text}">
        子午沖이 있어 가치관 차이는 솔직히 표시됩니다.</text>
      <text x="${W*0.025}" y="${W*0.17}"
            font-family="${F_SANS}" font-size="${W*0.027}" fill="${C.text}">
        오행 보완 +0.18 — 서로의 결손을 채우는 경향.</text>

      <!-- 주의 / 관점 -->
      <g transform="translate(${W*0.025}, ${W*0.22})">
        <rect width="${innerW - W*0.10}" height="${W*0.085}"
              rx="${W*0.008}" fill="${C.bg}" stroke="${C.bad}"/>
        <text x="${W*0.015}" y="${W*0.025}"
              font-family="${F_SERIF}" font-size="${W*0.022}" fill="${C.warn}"
              letter-spacing="${W*0.005}">주의 — 학파별 견해 갈림</text>
        <text x="${W*0.015}" y="${W*0.058}"
              font-family="${F_SANS}" font-size="${W*0.024}" fill="${C.text2}">
          ◦ 일주 60갑자 궁합표는 잠정 — 자문위원 검증 권장</text>
      </g>
    </g>

    ${footer(W, H)}
  </svg>`;
}

// ── 스크린샷 6 · 결정 도우미 A/B ───────────────────────────
function screenDecision(W, H) {
  const contentY = H * 0.20;
  const contentH = H * 0.66;
  const padX = W * 0.10;
  const innerW = W - padX * 2;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    <rect width="${W}" height="${H}" fill="${C.bg}"/>

    ${header(W, H, "決 · 결정 도우미", "A vs B 선택지 자문", "사주 관점에서 두 옵션 비교")}
    ${frame(W, H, contentY, contentH)}

    <!-- A/B 옵션 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.04})">
      ${[
        { tag: "選 옵션 A", title: "이직 · A회사 SaaS", desc: "연봉 +20%, 새 도메인, 결정권 큼", lean: false },
        { tag: "選 옵션 B", title: "잔류 · 시니어 트랙", desc: "안정·인맥 자산, 6개월 후 승진", lean: true },
      ].map((opt, i) => `
        <g transform="translate(${i * (innerW * 0.51 + W*0.01)}, 0)">
          <rect width="${innerW*0.49}" height="${H*0.15}"
                rx="${W*0.018}"
                fill="${opt.lean ? "rgba(201,169,97,0.10)" : C.surface}"
                stroke="${opt.lean ? C.gold : C.line}"
                stroke-width="${opt.lean ? 2 : 1}"/>
          <text x="${W*0.025}" y="${W*0.04}"
                font-family="${F_SERIF}" font-size="${W*0.024}" fill="${C.gold}"
                letter-spacing="${W*0.005}">${opt.tag}</text>
          <text x="${W*0.025}" y="${W*0.085}"
                font-family="${F_SERIF}" font-size="${W*0.034}" fill="${C.text}"
                font-weight="700">${opt.title}</text>
          <text x="${W*0.025}" y="${W*0.12}"
                font-family="${F_SANS}" font-size="${W*0.024}" fill="${C.text2}">${opt.desc}</text>
          ${opt.lean ? `
            <circle cx="${innerW*0.49 - W*0.04}" cy="${W*0.04}" r="${W*0.018}"
                    fill="${C.gold}"/>
            <text x="${innerW*0.49 - W*0.04}" y="${W*0.048}"
                  font-family="${F_SERIF}" font-size="${W*0.022}" fill="${C.bg}"
                  font-weight="900" text-anchor="middle">★</text>
          ` : ""}
        </g>
      `).join("")}
    </g>

    <!-- Lean 배지 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.21})">
      <rect width="${innerW - W*0.05}" height="${W*0.07}"
            rx="${W*0.012}" fill="${C.surface2}" stroke="${C.gold}" stroke-width="1.5"/>
      <text x="${W*0.025}" y="${W*0.048}"
            font-family="${F_SERIF}" font-size="${W*0.028}" fill="${C.gold}"
            font-weight="700">B 쪽으로 살짝 기움 · 신뢰도 medium</text>
    </g>

    <!-- 비교 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.29})">
      <rect width="${innerW - W*0.05}" height="${H*0.12}"
            rx="${W*0.014}" fill="${C.surface}" stroke="${C.line}"/>
      <text x="${W*0.02}" y="${W*0.04}"
            font-family="${F_SERIF}" font-size="${W*0.024}" fill="${C.gold}"
            letter-spacing="${W*0.005}">A · B 비교</text>
      <text x="${W*0.02}" y="${W*0.075}"
            font-family="${F_SANS}" font-size="${W*0.026}" fill="${C.text2}">
        庚午대운에 들어서면 관성이 강화됩니다.</text>
      <text x="${W*0.02}" y="${W*0.105}"
            font-family="${F_SANS}" font-size="${W*0.026}" fill="${C.text2}">
        잔류 시 안정과 성장의 결이 자연스러워 보입니다.</text>
      <text x="${W*0.02}" y="${W*0.135}"
            font-family="${F_SANS}" font-size="${W*0.026}" fill="${C.text2}">
        이직 시 도전의 흐름이 강해지나 부담도 함께 큽니다.</text>
    </g>

    <!-- 종합 자문 -->
    <g transform="translate(${padX + W*0.025}, ${contentY + H*0.43})">
      <rect width="${innerW - W*0.05}" height="${H*0.13}"
            rx="${W*0.018}" fill="${C.surface2}" stroke="${C.gold}" stroke-width="2"/>
      <text x="${W*0.025}" y="${W*0.04}"
            font-family="${F_SERIF}" font-size="${W*0.024}" fill="${C.gold}"
            letter-spacing="${W*0.005}">종합 자문</text>
      <text x="${W*0.025}" y="${W*0.085}"
            font-family="${F_SERIF}" font-size="${W*0.030}" fill="${C.text}"
            font-weight="700">최종 결정은 본인이 합니다 — 자평은 결정의 결을</text>
      <text x="${W*0.025}" y="${W*0.12}"
            font-family="${F_SERIF}" font-size="${W*0.030}" fill="${C.text}"
            font-weight="700">짚는 자문 도구입니다.</text>
    </g>

    ${footer(W, H)}
  </svg>`;
}

// ── 빌더 ──────────────────────────────────────────────────
const SCREENS = [
  { name: "1-hero", fn: screenHero },
  { name: "2-saju", fn: screenSaju },
  { name: "3-life-flow", fn: screenLifeFlow },
  { name: "4-ai-consult", fn: screenAiConsult },
  { name: "5-compatibility", fn: screenCompat },
  { name: "6-decision", fn: screenDecision },
];

const PLATFORMS = [
  { name: "ios", W: 1290, H: 2796 },       // iPhone 14 Pro Max
  { name: "android", W: 1080, H: 1920 },   // Play Store phone
];

async function build() {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

  for (const platform of PLATFORMS) {
    for (const screen of SCREENS) {
      const svg = screen.fn(platform.W, platform.H);
      const outPath = path.join(OUT_DIR, `${platform.name}-${screen.name}.png`);
      await sharp(Buffer.from(svg))
        .resize(platform.W, platform.H)
        .png({ quality: 100, compressionLevel: 9 })
        .toFile(outPath);
      console.log(`✓ ${path.basename(outPath)}  ${platform.W}×${platform.H}`);
    }
  }
  console.log(`\n✅ ${PLATFORMS.length * SCREENS.length} screenshots generated.`);
  console.log(`📁 ${OUT_DIR}`);
}

build().catch(e => { console.error(e); process.exit(1); });

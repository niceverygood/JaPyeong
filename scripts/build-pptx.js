/**
 * 자평 × TM 파트너십 PPTX 생성 — v2 (4티어 + SKU 분리).
 *
 * 산출물: docs/sales/tm-partnership-pitch.pptx
 *
 * 실행: NODE_PATH=/Users/seungsoohan/.npm-global/lib/node_modules node scripts/build-pptx.js
 *
 * Dark + Gold 테마, 15 slides, Korean serif headings.
 * BM v2 반영: Premium 39만/Family 59만, 수수료 35/40%, SKU 분리, 자녀 사주 보류
 */

const pptxgen = require("pptxgenjs");

const C = {
  bg: "0E0F13",
  surface: "15171E",
  surface2: "1B1E27",
  gold: "C9A961",
  goldDim: "8C7838",
  text: "ECECEF",
  text2: "B7B8C0",
  textMut: "80828D",
  line: "2A2E3A",
  lineStrong: "3A3F4F",
  ok: "6CB58A",
  warn: "E0A858",
  bad: "D45D5D",
};

const F = {
  serif: "Noto Serif KR",
  sans: "Malgun Gothic",
  mono: "Menlo",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const W = 13.333, H = 7.5;
pres.author = "자평 운영팀";
pres.title = "자평 × TM 파트너십 제안서 v2";
pres.subject = "TM 파트너십 — Confidential · BM v2";

// ── 공통 헬퍼 ─────────────────────────────────────────────
function addBg(slide) { slide.background = { color: C.bg }; }

function addWatermark(slide, pageNum) {
  slide.addText("CONFIDENTIAL · PARTNERSHIP · v2", {
    x: W - 4.3, y: 0.22, w: 4.0, h: 0.3,
    fontSize: 9, fontFace: F.sans, color: C.goldDim,
    align: "right", charSpacing: 4, margin: 0,
  });
  slide.addText([
    { text: "子平", options: { fontFace: F.serif, bold: true, color: C.gold } },
    { text: "  ·  자평  ·  ", options: { fontFace: F.sans, color: C.textMut } },
    { text: `${pageNum} / 15`, options: { fontFace: F.sans, color: C.textMut } },
  ], {
    x: W - 4.3, y: H - 0.45, w: 4.0, h: 0.3,
    fontSize: 10, align: "right", margin: 0,
  });
}

function addPageTitle(slide, title, eyebrow) {
  if (eyebrow) {
    slide.addText(eyebrow, {
      x: 0.6, y: 0.5, w: 8, h: 0.3,
      fontSize: 10, fontFace: F.serif, color: C.gold,
      charSpacing: 8, margin: 0,
    });
  }
  slide.addText(title, {
    x: 0.6, y: 0.82, w: 12, h: 0.7,
    fontSize: 26, fontFace: F.serif, bold: true, color: C.text,
    margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.55, w: 0.6, h: 0.04,
    fill: { color: C.gold }, line: { type: "none" },
  });
}

// ── 1. 표지 ──────────────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  s.addText("CONFIDENTIAL · PARTNERSHIP · v2", {
    x: W - 4.3, y: 0.4, w: 4.0, h: 0.3,
    fontSize: 9, fontFace: F.sans, color: C.goldDim,
    align: "right", charSpacing: 4, margin: 0,
  });
  s.addText([
    { text: "子", options: { color: C.text } },
    { text: "平", options: { color: C.gold } },
  ], {
    x: 0, y: 1.4, w: W, h: 2.2,
    fontSize: 180, fontFace: F.serif, bold: true,
    align: "center", margin: 0,
  });
  s.addText("자 평  ·  J A P Y E O N G", {
    x: 0, y: 3.7, w: W, h: 0.4,
    fontSize: 14, fontFace: F.sans, color: C.text2,
    charSpacing: 16, align: "center", margin: 0,
  });
  s.addText("결정 앞에, 자평.", {
    x: 0, y: 4.3, w: W, h: 0.6,
    fontSize: 32, fontFace: F.serif, bold: true, color: C.text,
    align: "center", margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: W / 2 - 0.6, y: 5.2, w: 1.2, h: 0.04,
    fill: { color: C.gold }, line: { type: "none" },
  });
  s.addText("TM 파트너십 제안서  ·  v2", {
    x: 0, y: 5.35, w: W, h: 0.45,
    fontSize: 20, fontFace: F.serif, color: C.text,
    align: "center", margin: 0,
  });
  s.addText("Premium 39만 / Family 59만  ·  수수료 35~40%  ·  SKU 채널 분리", {
    x: 0, y: 5.85, w: W, h: 0.35,
    fontSize: 13, fontFace: F.sans, color: C.gold,
    align: "center", charSpacing: 4, margin: 0,
  });
  s.addText("자평 운영팀  ·  2026.06  ·  BM v2  ·  3중 적대적 검증 통합", {
    x: 0, y: H - 0.5, w: W, h: 0.3,
    fontSize: 10, fontFace: F.sans, color: C.textMut,
    align: "center", charSpacing: 4, margin: 0,
  });
}

// ── 2. Executive Summary ─────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "1분 안에 — 자평이 TM에 잘 맞는 이유", "禮 · Executive Summary");
  addWatermark(s, 2);

  const items = [
    { k: "제품", v: "AI 보조 고전 해석 +\n명리 자문위원 사주 SaaS" },
    { k: "TM 전용 단가", v: "Premium 39만 / Family 59만\n(연 일시불)" },
    { k: "TM 수수료", v: "Premium 35% (~13.6만)\nFamily 40% (~23.6만)" },
    { k: "건당 마진", v: "약 1.6 ~ 12만 원\n(CAC 12만 차감 후)" },
    { k: "운영 부담", v: "콜만 — 약관·환불·CS·법무\n자평이 100% 처리" },
    { k: "시작", v: "1개월 파일럿 (5명)\n자평 CPA 보전 5% 추가" },
  ];

  const gridX = 0.6, gridY = 1.95;
  const cardW = 4.0, cardH = 1.85, gap = 0.15;
  items.forEach((it, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = gridX + col * (cardW + gap);
    const y = gridY + row * (cardH + gap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: cardW, h: cardH,
      fill: { color: C.surface }, line: { color: C.line, width: 1 },
    });
    s.addText(it.k, {
      x: x + 0.3, y: y + 0.2, w: cardW - 0.6, h: 0.35,
      fontSize: 11, fontFace: F.serif, color: C.gold,
      charSpacing: 4, bold: true, margin: 0,
    });
    s.addText(it.v, {
      x: x + 0.3, y: y + 0.65, w: cardW - 0.6, h: cardH - 0.85,
      fontSize: 14, fontFace: F.sans, color: C.text,
      margin: 0, paraSpaceAfter: 4,
    });
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: H - 1.15, w: W - 1.2, h: 0.5,
    fill: { color: C.surface2 }, line: { color: C.goldDim, width: 1 },
  });
  s.addText(
    "SKU 물리적 분리(Basic/Std=Self-serve, Prem/Family=TM)  ·  자문위원 회차 독립  ·  법무 리스크 자평이 100% 헷지",
    {
      x: 0.6, y: H - 1.15, w: W - 1.2, h: 0.5,
      fontSize: 13, fontFace: F.serif, color: C.gold,
      align: "center", valign: "middle", margin: 0,
    });
}

// ── 3. 시장 기회 ──────────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "한국 사주 시장 — 1~4조 규모 추산, 디지털 5% 미만", "市 · 시장 기회");
  addWatermark(s, 3);

  const stats = [
    { v: "1~4조", k: "국내 사주·역학 시장 (추산)", sub: "공식 통계 부재 — 비공식 비중 큼" },
    { v: "5% 미만", k: "디지털 비중", sub: "대부분 오프라인 명리원·점집" },
    { v: "7~15만", k: "1회 명리원 상담가", sub: "자평 Premium 1년 = 명리원 3~5회" },
  ];

  stats.forEach((it, i) => {
    const x = 0.6 + i * 4.15;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.0, w: 3.95, h: 2.3,
      fill: { color: C.surface }, line: { color: C.line, width: 1 },
    });
    s.addText(it.v, {
      x: x, y: 2.25, w: 3.95, h: 1.05,
      fontSize: 48, fontFace: F.serif, bold: true, color: C.gold,
      align: "center", margin: 0,
    });
    s.addText(it.k, {
      x: x + 0.2, y: 3.35, w: 3.55, h: 0.45,
      fontSize: 14, fontFace: F.sans, color: C.text,
      align: "center", margin: 0,
    });
    s.addText(it.sub, {
      x: x + 0.2, y: 3.8, w: 3.55, h: 0.4,
      fontSize: 10, fontFace: F.sans, color: C.textMut,
      align: "center", margin: 0,
    });
  });

  s.addText("핵심 타겟  ·  40~60대 여성 (자평 본진)", {
    x: 0.6, y: 4.8, w: W - 1.2, h: 0.45,
    fontSize: 18, fontFace: F.serif, bold: true, color: C.text,
    align: "center", charSpacing: 4, margin: 0,
  });
  s.addText("가족·자녀·결혼·이주 의사결정 게이트키퍼  ·  TM 채널 인구·매체 행동·결제 패턴과 일치", {
    x: 0.6, y: 5.3, w: W - 1.2, h: 0.45,
    fontSize: 13, fontFace: F.sans, color: C.text2,
    align: "center", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 1.4, y: 6.05, w: W - 2.8, h: 0.7,
    fill: { color: C.surface2 }, line: { color: C.goldDim, width: 1 },
  });
  s.addText(
    "자평 wedge: 상위 20% '의사결정 자문' 카테고리  ·  락인 후 매출 다변화 (B2B·자문위원·시즌)",
    {
      x: 1.4, y: 6.05, w: W - 2.8, h: 0.7,
      fontSize: 13, fontFace: F.serif, color: C.gold,
      align: "center", valign: "middle", margin: 0,
    });
}

// ── 4. 자평 3층 구조 ────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "자평 3층 구조 — 모방 어려운 조합", "本 · 자평이란");
  addWatermark(s, 4);

  const layers = [
    {
      n: "Layer 1",
      title: "룰베이스 명리 엔진",
      sub: "결정론적 · Deterministic",
      body: "절기·진태양시·60갑자·격국·용신·대운을 코드가 확정.\nAI가 사주를 푸는 게 아닙니다 — 코드가 먼저 사주를 세우고 AI는 그 위에서 해석만 합니다.",
      tag: "회귀 테스트 316건 통과",
    },
    {
      n: "Layer 2",
      title: "AI 보조 고전 해석",
      sub: "고전 인용 의무 · 학파 다양성",
      body: "엔진 결과 위에서 해석만. 연해자평·삼명통회·적천수 출처 표기.\n학파별 견해가 갈리는 부분은 'contested' 필드로 솔직히 명시.",
      tag: "단정 표현 자동 톤다운",
    },
    {
      n: "Layer 3",
      title: "명리 자문위원 (사람)",
      sub: "3년 독점 계약 + 위약금",
      body: "Premium/Family에서 1:1 검증·상담.\n자평이 영입한 5~50명 풀과 3년 독점 계약 — 경쟁사 카피 불가의 실질 해자.",
      tag: "진짜 해자 ❷",
    },
  ];

  const layerY = 2.0, layerH = 1.55, gap = 0.2;
  layers.forEach((l, i) => {
    const y = layerY + i * (layerH + gap);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y, w: W - 1.2, h: layerH,
      fill: { color: C.surface }, line: { color: C.line, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y, w: 0.08, h: layerH,
      fill: { color: C.gold }, line: { type: "none" },
    });
    s.addText(l.n, {
      x: 0.95, y: y + 0.18, w: 1.6, h: 0.3,
      fontSize: 11, fontFace: F.serif, color: C.gold,
      charSpacing: 4, bold: true, margin: 0,
    });
    s.addText(l.title, {
      x: 0.95, y: y + 0.48, w: 4.5, h: 0.45,
      fontSize: 17, fontFace: F.serif, bold: true, color: C.text,
      margin: 0,
    });
    s.addText(l.sub, {
      x: 0.95, y: y + 0.95, w: 4.5, h: 0.32,
      fontSize: 11, fontFace: F.sans, color: C.textMut,
      margin: 0,
    });
    s.addText(l.body, {
      x: 5.7, y: y + 0.22, w: 5.5, h: layerH - 0.5,
      fontSize: 12, fontFace: F.sans, color: C.text2,
      margin: 0, paraSpaceAfter: 4,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 11.3, y: y + layerH / 2 - 0.22, w: 1.65, h: 0.44,
      fill: { color: C.surface2 }, line: { color: C.goldDim, width: 1 },
    });
    s.addText(l.tag, {
      x: 11.3, y: y + layerH / 2 - 0.22, w: 1.65, h: 0.44,
      fontSize: 9, fontFace: F.sans, color: C.gold,
      align: "center", valign: "middle", margin: 0,
    });
  });
}

// ── 5. 라이브 기능 6종 ────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "지금 라이브로 작동하는 기능 — 데모 가능", "用 · 라이브 기능");
  addWatermark(s, 5);

  const feats = [
    { g: "命", t: "사주 명식 분석", d: "8자·십성·오행·격국·용신 자동 산출" },
    { g: "流", t: "인생 흐름 그래프", d: "대운 80년 길흉 시각화 (-5~+5 점수)" },
    { g: "問", t: "12 카테고리 AI 자문", d: "직업·결혼·자녀·재정 등 단일 클릭 풀이" },
    { g: "宮", t: "궁합 (宮合)", d: "두 사주 비교 + 학파별 견해 표시" },
    { g: "擇", t: "택일 (擇日)", d: "기간 내 좋은 날 추천 (행사 유형별 보너스)" },
    { g: "決", t: "결정 도우미 A/B", d: "두 선택지 사주 비교 + lean 표시" },
  ];

  const gridX = 0.6, gridY = 2.0;
  const cardW = 4.0, cardH = 2.0, gap = 0.15;
  feats.forEach((f, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = gridX + col * (cardW + gap);
    const y = gridY + row * (cardH + gap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: cardW, h: cardH,
      fill: { color: C.surface }, line: { color: C.line, width: 1 },
    });
    s.addText(f.g, {
      x: x + 0.3, y: y + 0.25, w: 0.9, h: 0.9,
      fontSize: 44, fontFace: F.serif, bold: true, color: C.gold,
      margin: 0,
    });
    s.addText(f.t, {
      x: x + 1.25, y: y + 0.4, w: cardW - 1.45, h: 0.45,
      fontSize: 16, fontFace: F.serif, bold: true, color: C.text,
      margin: 0,
    });
    s.addText(f.d, {
      x: x + 0.3, y: y + 1.25, w: cardW - 0.6, h: 0.65,
      fontSize: 11.5, fontFace: F.sans, color: C.text2,
      margin: 0,
    });
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 6.45, w: W - 1.2, h: 0.55,
    fill: { color: C.surface2 }, line: { color: C.goldDim, width: 1 },
  });
  s.addText([
    { text: "데모: ", options: { color: C.text2 } },
    { text: "https://ja-pyeong.vercel.app", options: { color: C.gold, bold: true } },
    { text: "  ·  무료 체험 회원가입 불필요 · 모바일·PC 모두 가능", options: { color: C.text2 } },
  ], {
    x: 0.6, y: 6.45, w: W - 1.2, h: 0.55,
    fontSize: 13, fontFace: F.sans, align: "center", valign: "middle", margin: 0,
  });
}

// ── 6. 왜 TM인가 — 단가 비교표 (업데이트) ─────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "다른 TM 상품 대비 단가·마진이 두꺼움", "比 · 왜 TM 채널인가");
  addWatermark(s, 6);

  const rows = [
    { name: "알뜰폰 요금제", price: "3~5만", commission: "0.9~1.5만", margin: "(-)", featured: false },
    { name: "인터넷·IPTV 약정", price: "20~40만", commission: "6~12만", margin: "-4 ~ 2만", featured: false },
    { name: "보험 부가 특약", price: "40~80만", commission: "8~24만", margin: "-2 ~ 14만", featured: false },
    { name: "온라인 강의 1년", price: "20~50만", commission: "4~15만", margin: "-6 ~ 5만", featured: false },
    { name: "자평 Premium  ★", price: "39만", commission: "13.6만 (35%)", margin: "1.6만", featured: true, ours: true },
    { name: "자평 Family  ★", price: "59만", commission: "23.6만 (40%)", margin: "10만+", featured: true, ours: true },
  ];

  const headerY = 1.95;
  const cols = [
    { x: 0.6, w: 3.6, label: "상품" },
    { x: 4.3, w: 2.4, label: "계약가" },
    { x: 6.8, w: 2.9, label: "TM 수수료" },
    { x: 9.8, w: 2.9, label: "건당 마진 (CAC 10만)" },
  ];
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: headerY, w: W - 1.2, h: 0.5,
    fill: { color: C.surface2 }, line: { color: C.line, width: 0.5 },
  });
  cols.forEach(c => {
    s.addText(c.label, {
      x: c.x, y: headerY, w: c.w, h: 0.5,
      fontSize: 12, fontFace: F.serif, bold: true, color: C.gold,
      align: "center", valign: "middle", charSpacing: 4, margin: 0,
    });
  });

  rows.forEach((r, i) => {
    const y = 2.5 + i * 0.62;
    const bg = r.featured ? C.surface2 : C.surface;
    const txtColor = r.featured ? C.gold : (r.ours ? C.text : C.text2);
    const fontWeight = r.featured;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y, w: W - 1.2, h: 0.62,
      fill: { color: bg }, line: { color: C.line, width: 0.5 },
    });
    if (r.featured) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.6, y, w: 0.06, h: 0.62,
        fill: { color: C.gold }, line: { type: "none" },
      });
    }
    s.addText(r.name, {
      x: cols[0].x + 0.2, y, w: cols[0].w - 0.2, h: 0.62,
      fontSize: 13, fontFace: F.serif, bold: r.ours, color: txtColor,
      align: "left", valign: "middle", margin: 0,
    });
    s.addText(r.price, {
      x: cols[1].x, y, w: cols[1].w, h: 0.62,
      fontSize: 13, fontFace: F.sans, bold: fontWeight, color: txtColor,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(r.commission, {
      x: cols[2].x, y, w: cols[2].w, h: 0.62,
      fontSize: 13, fontFace: F.sans, bold: fontWeight, color: txtColor,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(r.margin, {
      x: cols[3].x, y, w: cols[3].w, h: 0.62,
      fontSize: 13, fontFace: F.sans, bold: fontWeight, color: txtColor,
      align: "center", valign: "middle", margin: 0,
    });
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 6.5, w: W - 1.2, h: 0.55,
    fill: { color: C.surface2 }, line: { color: C.gold, width: 1 },
  });
  s.addText("Premium/Family가 핵심 수익원  ·  볼륨 보너스·갱신 수수료로 LTV 확보", {
    x: 0.6, y: 6.5, w: W - 1.2, h: 0.55,
    fontSize: 12, fontFace: F.serif, color: C.gold,
    align: "center", valign: "middle", margin: 0,
  });
}

// ── 7. 상품 4티어 (SKU 분리) ───────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "4티어 · SKU 채널 물리적 분리", "品 · 상품 구성");
  addWatermark(s, 7);

  const tiers = [
    {
      name: "BASIC · 자가",
      sub: "Self-serve only · TM 비대상",
      price: "49,000",
      monthly: "월 환산 4,083원",
      featured: false, dimmed: true,
      feats: ["AI 리포트 (공정 사용)", "일진 알림", "월간 요약"],
      commission: "TM 비대상",
    },
    {
      name: "STANDARD · 자가",
      sub: "Self-serve only · TM 비대상",
      price: "149,000",
      monthly: "월 환산 12,416원",
      featured: false, dimmed: true,
      feats: ["Basic 전체 포함", "결정 도우미 무제한", "상세 통변·궁합 5건"],
      commission: "TM 비대상",
    },
    {
      name: "PREMIUM (1:1) ★",
      sub: "TM 핵심 클로징",
      price: "390,000",
      monthly: "월 환산 32,500원",
      featured: true, dimmed: false,
      feats: ["Standard 전체 포함", "자문위원 1:1 연 2회", "학파 교차 검토"],
      commission: "TM 수수료 (35%): 136,500원",
    },
    {
      name: "FAMILY · TM 우선 ★",
      sub: "가족 4인 + 자문위원 통합",
      price: "590,000",
      monthly: "월 환산 49,166원",
      featured: true, dimmed: false,
      feats: ["가족 4인 AI 분석", "자문위원 통합 2회 (가족 무관)", "택일 컨설팅 무제한"],
      commission: "TM 수수료 (40%): 236,000원",
    },
  ];

  const tierY = 1.95;
  const tierW = 3.0, tierH = 5.2, gap = 0.12;
  tiers.forEach((t, i) => {
    const x = 0.6 + i * (tierW + gap);
    const cardOpacity = t.dimmed ? 0.55 : 1.0;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: tierY, w: tierW, h: tierH,
      fill: { color: t.featured ? C.surface2 : C.surface },
      line: { color: t.featured ? C.gold : C.line, width: t.featured ? 2 : 1 },
    });
    s.addText(t.name, {
      x: x + 0.2, y: tierY + 0.2, w: tierW - 0.4, h: 0.32,
      fontSize: 10, fontFace: F.serif, bold: true,
      color: t.dimmed ? C.textMut : C.gold,
      charSpacing: 3, margin: 0,
    });
    s.addText(t.sub, {
      x: x + 0.2, y: tierY + 0.55, w: tierW - 0.4, h: 0.3,
      fontSize: 10, fontFace: F.sans, color: t.dimmed ? C.textMut : C.text2, margin: 0,
    });
    s.addText([
      { text: t.price, options: { fontSize: 26, color: t.dimmed ? C.textMut : C.text, bold: true } },
      { text: "원/년", options: { fontSize: 11, color: t.dimmed ? C.textMut : C.text2 } },
    ], {
      x: x + 0.2, y: tierY + 1.0, w: tierW - 0.4, h: 0.7,
      fontFace: F.serif, margin: 0,
    });
    s.addText(t.monthly, {
      x: x + 0.2, y: tierY + 1.75, w: tierW - 0.4, h: 0.3,
      fontSize: 10, fontFace: F.sans, color: C.textMut, margin: 0,
    });
    s.addShape(pres.shapes.LINE, {
      x: x + 0.2, y: tierY + 2.2, w: tierW - 0.4, h: 0,
      line: { color: C.line, width: 0.5 },
    });
    s.addText(
      t.feats.map((f, idx) => ({
        text: f,
        options: { bullet: { code: "25CF" }, color: t.dimmed ? C.textMut : C.text, breakLine: idx < t.feats.length - 1 },
      })),
      {
        x: x + 0.2, y: tierY + 2.35, w: tierW - 0.4, h: 2.0,
        fontSize: 11, fontFace: F.sans, paraSpaceAfter: 6, margin: 0,
      }
    );
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.2, y: tierY + tierH - 0.7, w: tierW - 0.4, h: 0.45,
      fill: { color: t.featured ? C.bg : (t.dimmed ? C.bg : C.surface2) },
      line: { color: t.dimmed ? C.line : C.goldDim, width: 1 },
    });
    s.addText(t.commission, {
      x: x + 0.2, y: tierY + tierH - 0.7, w: tierW - 0.4, h: 0.45,
      fontSize: 10, fontFace: F.serif, bold: !t.dimmed,
      color: t.dimmed ? C.textMut : C.gold,
      align: "center", valign: "middle", margin: 0,
    });
  });
}

// ── 8. 가격 정당화 ───────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "왜 39만~59만 원이어도 합리적인가", "義 · 가격 정당화");
  addWatermark(s, 8);

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 1.95, w: 5.7, h: 4.4,
    fill: { color: C.surface }, line: { color: C.line, width: 1 },
  });
  s.addText("동네 명리원  ·  1회 상담", {
    x: 0.8, y: 2.15, w: 5.7, h: 0.4,
    fontSize: 13, fontFace: F.serif, color: C.textMut,
    align: "center", charSpacing: 4, margin: 0,
  });
  s.addText("7~15만 원", {
    x: 0.8, y: 2.7, w: 5.7, h: 1.0,
    fontSize: 52, fontFace: F.serif, bold: true, color: C.text,
    align: "center", margin: 0,
  });
  s.addText("· 그 자리에서 한 번\n· 다음 결정 때 다시 비용\n· 학파 한 곳 의견\n· 사주 풀이 + 끝", {
    x: 1.0, y: 4.0, w: 5.3, h: 2.0,
    fontSize: 13, fontFace: F.sans, color: C.text2,
    paraSpaceAfter: 6, margin: 0,
  });

  s.addText("VS", {
    x: 6.5, y: 3.7, w: 0.5, h: 0.5,
    fontSize: 18, fontFace: F.serif, bold: true, color: C.gold,
    align: "center", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.0, y: 1.95, w: 5.7, h: 4.4,
    fill: { color: C.surface2 }, line: { color: C.gold, width: 2 },
  });
  s.addText("자평 Premium (TM 전용)", {
    x: 7.0, y: 2.15, w: 5.7, h: 0.4,
    fontSize: 13, fontFace: F.serif, color: C.gold,
    align: "center", charSpacing: 4, bold: true, margin: 0,
  });
  s.addText("39만 원 / 1년", {
    x: 7.0, y: 2.7, w: 5.7, h: 1.0,
    fontSize: 52, fontFace: F.serif, bold: true, color: C.text,
    align: "center", margin: 0,
  });
  s.addText("· 1년 365일 무제한 (공정 사용)\n· 분기 종합 PDF 리포트 4건\n· 학파별 견해 + 고전 인용\n· 자문위원 1:1 전화 연 2회", {
    x: 7.2, y: 4.0, w: 5.3, h: 2.0,
    fontSize: 13, fontFace: F.sans, color: C.text,
    paraSpaceAfter: 6, margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 6.45, w: W - 1.6, h: 0.55,
    fill: { color: C.surface2 }, line: { color: C.gold, width: 1 },
  });
  s.addText("명리원 1회 비용 × 3~5회  =  자평 Premium 1년  +  자문위원 1:1 두 번", {
    x: 0.8, y: 6.45, w: W - 1.6, h: 0.55,
    fontSize: 13, fontFace: F.serif, color: C.gold,
    align: "center", valign: "middle", margin: 0,
  });
}

// ── 9. 파트너십 조건 ──────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "협의 출발점 — 첫 미팅에서 조정 가능", "約 · 파트너십 조건");
  addWatermark(s, 9);

  const conds = [
    { k: "Premium 수수료", v: "35%  ·  136,500원/건", sub: "협의 범위 30~40%" },
    { k: "Family 수수료", v: "40%  ·  236,000원/건", sub: "협의 범위 35~45%" },
    { k: "갱신 수수료", v: "1년차 갱신 10%", sub: "LTV 보상 — 단순 신규 가입 외 추가" },
    { k: "볼륨 보너스", v: "월 50건 +5% / 100건 +10%", sub: "회사 규모별 인센티브" },
    { k: "청약철회 회수", v: "7일 100% / ~30일 50% / ~90일 25%", sub: "단계별 회수 — 90일 이후 0%" },
    { k: "파일럿 보전", v: "첫 30일 CPA 5% 추가", sub: "100건 미달 시 자평이 보전" },
  ];

  conds.forEach((c, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15;
    const y = 1.95 + row * 1.65;
    const cardW = 6.0, cardH = 1.5;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: cardW, h: cardH,
      fill: { color: C.surface }, line: { color: C.line, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h: cardH,
      fill: { color: C.gold }, line: { type: "none" },
    });
    s.addText(c.k, {
      x: x + 0.25, y: y + 0.18, w: 2.5, h: 0.35,
      fontSize: 11, fontFace: F.serif, color: C.gold,
      charSpacing: 4, bold: true, margin: 0,
    });
    s.addText(c.v, {
      x: x + 0.25, y: y + 0.5, w: cardW - 0.4, h: 0.5,
      fontSize: 15, fontFace: F.serif, bold: true, color: C.text, margin: 0,
    });
    s.addText(c.sub, {
      x: x + 0.25, y: y + 1.0, w: cardW - 0.4, h: 0.4,
      fontSize: 11, fontFace: F.sans, color: C.text2, margin: 0,
    });
  });
}

// ── 10. 책임 분리 ────────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "책임 분리 — TM은 콜에만 집중", "分 · 역할 분담");
  addWatermark(s, 10);

  const left = {
    title: "자평이 책임",
    items: [
      "제품 (앱 · 자문위원 · 서버)",
      "결제 시스템 (토스 · 카카오페이)",
      "약관 · 환불 · CS",
      "법무 · 표시광고 사전 검수",
      "금지어 CI 훅 (양사 카피 자동 검수)",
      "완성된 TM 스크립트 + 4+6시간 무상 교육",
      "CRM 대시보드 · 마케팅 자료",
      "자녀 사주 출시 보류 (윤리)",
    ],
  };
  const right = {
    title: "TM이 책임",
    items: [
      "콜센터 운영 (상담사·DB·녹취)",
      "자평 지정 멘트 준수",
      "녹취 5년 보관",
      "1차 응대 (가입자 콜백)",
      "주 1회 KPI 보고 (티어 믹스 포함)",
    ],
  };

  const cardTop = 1.95, cardH = 4.4;

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: cardTop, w: 6.0, h: cardH,
    fill: { color: C.surface }, line: { color: C.gold, width: 2 },
  });
  s.addText(left.title, {
    x: 0.6, y: cardTop + 0.2, w: 6.0, h: 0.5,
    fontSize: 18, fontFace: F.serif, bold: true, color: C.gold,
    align: "center", margin: 0,
  });
  s.addShape(pres.shapes.LINE, {
    x: 2.6, y: cardTop + 0.8, w: 2.0, h: 0,
    line: { color: C.gold, width: 1 },
  });
  s.addText(
    left.items.map((t, idx) => ({
      text: t,
      options: { bullet: { code: "25A0" }, color: C.text, breakLine: idx < left.items.length - 1 },
    })),
    {
      x: 1.1, y: cardTop + 1.05, w: 5.0, h: cardH - 1.2,
      fontSize: 12, fontFace: F.sans, paraSpaceAfter: 4, margin: 0,
    });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.75, y: cardTop, w: 6.0, h: cardH,
    fill: { color: C.surface2 }, line: { color: C.line, width: 1 },
  });
  s.addText(right.title, {
    x: 6.75, y: cardTop + 0.2, w: 6.0, h: 0.5,
    fontSize: 18, fontFace: F.serif, bold: true, color: C.text2,
    align: "center", margin: 0,
  });
  s.addShape(pres.shapes.LINE, {
    x: 8.75, y: cardTop + 0.8, w: 2.0, h: 0,
    line: { color: C.textMut, width: 1 },
  });
  s.addText(
    right.items.map((t, idx) => ({
      text: t,
      options: { bullet: { code: "25A1" }, color: C.text, breakLine: idx < right.items.length - 1 },
    })),
    {
      x: 7.25, y: cardTop + 1.05, w: 5.0, h: cardH - 1.2,
      fontSize: 13, fontFace: F.sans, paraSpaceAfter: 6, margin: 0,
    });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: cardTop + cardH + 0.2, w: W - 1.2, h: 0.55,
    fill: { color: C.bg }, line: { color: C.gold, width: 1 },
  });
  s.addText("법적 책임·환불 회수·민원·자녀 윤리는 자평이 100% 떠안는 구조  ·  TM은 콜만", {
    x: 0.6, y: cardTop + cardH + 0.2, w: W - 1.2, h: 0.55,
    fontSize: 12, fontFace: F.serif, color: C.gold,
    align: "center", valign: "middle", margin: 0,
  });
}

// ── 11. 단위 경제학 v2 ────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "월 100건 가입 시 — TM 대행사 수익 시뮬레이션", "算 · 단위 경제학");
  addWatermark(s, 11);

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.95, w: 5.7, h: 5.0,
    fill: { color: C.surface }, line: { color: C.line, width: 1 },
  });
  s.addText("가입 1건  ·  Premium (수수료 35%)", {
    x: 0.6, y: 2.1, w: 5.7, h: 0.4,
    fontSize: 12, fontFace: F.serif, color: C.gold,
    align: "center", charSpacing: 4, bold: true, margin: 0,
  });
  const left = [
    ["TM 수수료 (390k × 35%)", "+ 136,500", C.text],
    ["콜센터 운영비\n(콘택트 20:1, 5,000원)", "- 100,000", C.text2],
    ["첫 달 청약철회 (15%)", "- 20,475", C.text2],
  ];
  left.forEach((r, i) => {
    const y = 2.7 + i * 0.85;
    s.addText(r[0], {
      x: 0.9, y, w: 3.0, h: 0.7,
      fontSize: 12, fontFace: F.sans, color: r[2], valign: "middle", margin: 0,
    });
    s.addText(r[1], {
      x: 3.9, y, w: 2.0, h: 0.7,
      fontSize: 15, fontFace: F.serif, bold: true, color: r[2],
      align: "right", valign: "middle", margin: 0,
    });
  });
  s.addShape(pres.shapes.LINE, {
    x: 0.9, y: 5.55, w: 5.0, h: 0, line: { color: C.gold, width: 1 },
  });
  s.addText("건당 순마진", {
    x: 0.9, y: 5.65, w: 3.0, h: 0.7,
    fontSize: 14, fontFace: F.serif, bold: true, color: C.gold, valign: "middle", margin: 0,
  });
  s.addText("+ 16,025원", {
    x: 3.9, y: 5.65, w: 2.0, h: 0.7,
    fontSize: 22, fontFace: F.serif, bold: true, color: C.gold,
    align: "right", valign: "middle", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.55, y: 1.95, w: 6.2, h: 5.0,
    fill: { color: C.surface2 }, line: { color: C.gold, width: 2 },
  });
  s.addText("월 100건 가입  ·  Premium 70 + Family 30 믹스", {
    x: 6.55, y: 2.1, w: 6.2, h: 0.4,
    fontSize: 12, fontFace: F.serif, color: C.gold,
    align: "center", charSpacing: 4, bold: true, margin: 0,
  });
  const right = [
    ["Premium 70건 (×35%)", "+ 9,555,000", C.text],
    ["Family 30건 (×40%)", "+ 7,080,000", C.text],
    ["콜센터 운영비 (100 × 100k)", "- 10,000,000", C.text2],
    ["청약철회 (15%)", "- 2,495,250", C.text2],
  ];
  right.forEach((r, i) => {
    const y = 2.7 + i * 0.6;
    s.addText(r[0], {
      x: 6.85, y, w: 3.0, h: 0.5,
      fontSize: 12, fontFace: F.sans, color: r[2], valign: "middle", margin: 0,
    });
    s.addText(r[1], {
      x: 9.85, y, w: 2.7, h: 0.5,
      fontSize: 14, fontFace: F.serif, bold: true, color: r[2],
      align: "right", valign: "middle", margin: 0,
    });
  });
  s.addShape(pres.shapes.LINE, {
    x: 6.85, y: 5.5, w: 5.7, h: 0, line: { color: C.gold, width: 1 },
  });
  s.addText("월 순마진", {
    x: 6.85, y: 5.6, w: 3.0, h: 0.7,
    fontSize: 14, fontFace: F.serif, bold: true, color: C.gold, valign: "middle", margin: 0,
  });
  s.addText("+ 4,139,750원", {
    x: 9.5, y: 5.6, w: 3.05, h: 0.7,
    fontSize: 24, fontFace: F.serif, bold: true, color: C.gold,
    align: "right", valign: "middle", margin: 0,
  });
  s.addText("상담사 5명 → 본 운영(20명) 시 월 1.5천만 원대 가능", {
    x: 6.55, y: 6.45, w: 6.2, h: 0.3,
    fontSize: 10, fontFace: F.sans, color: C.textMut,
    align: "center", margin: 0,
  });
}

// ── 12. 리스크 매트릭스 ──────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "TM 대표가 가장 걱정할 8개 리스크 — 자평이 헷지", "守 · 리스크 & 컴플라이언스");
  addWatermark(s, 12);

  const rows = [
    ["리스크", "자평의 대응"],
    ["표시광고법 (부당 표시)", "자평 사전 검수 멘트만 + 금지어 CI 훅. 위반 시 자평 1차 책임"],
    ["전자상거래법 (청약철회)", "7일 100% 환불 보장. 결제·환불 자평이 운영"],
    ["통신판매법 (녹취·고지)", "자평 약관·고지 멘트 공급. 녹취만 TM 보관"],
    ["개인정보보호법", "자평 PIMS 수준 보안. TM은 결제 링크만 전송"],
    ["다크패턴 (자동갱신)", "opt-in 디폴트 OFF. 갱신 30/7/1일 전 3회 알림"],
    ["위기 키워드 (자살·자해)", "자평 가드레일 즉시 1393 안내로 단축"],
    ["환불 분쟁 회수", "자평 100% 처리. TM은 회수 책임 없음"],
    ["자녀 사주 윤리", "자녀 상품 6개월 출시 보류 (D-Day 시나리오 차단)"],
  ];

  const tableData = rows.map((row, ri) => row.map((cell, ci) => {
    if (ri === 0) {
      return {
        text: cell, options: {
          fill: { color: C.surface2 }, color: C.gold, bold: true,
          fontSize: 12, fontFace: F.serif, align: "center", valign: "middle",
          charSpacing: 4,
        }
      };
    }
    return {
      text: cell, options: {
        fontSize: 11.5, fontFace: ci === 0 ? F.serif : F.sans,
        color: ci === 0 ? C.text : C.text2,
        bold: ci === 0,
        align: "left", valign: "middle",
        margin: [4, 8, 4, 8],
      }
    };
  }));

  s.addTable(tableData, {
    x: 0.6, y: 1.95, w: W - 1.2,
    colW: [4.5, 7.62], rowH: 0.48,
    border: { type: "solid", pt: 0.5, color: C.line },
    fill: { color: C.surface },
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 6.3, w: W - 1.2, h: 0.55,
    fill: { color: C.surface2 }, line: { color: C.gold, width: 1 },
  });
  s.addText("TM이 안고 가던 법적 책임·환불 회수·민원·윤리 부담을 자평이 제도적으로 떠안는 구조", {
    x: 0.6, y: 6.3, w: W - 1.2, h: 0.55,
    fontSize: 12, fontFace: F.serif, color: C.gold,
    align: "center", valign: "middle", margin: 0,
  });
}

// ── 13. 로드맵 ───────────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "함께 만들 3단계 — 파일럿부터 확장까지", "圖 · 로드맵");
  addWatermark(s, 13);

  const phases = [
    {
      tag: "Phase 1", period: "1개월 · 파일럿", title: "검증",
      body: "상담사 5명 · 일일 콜 2,000건\n가입 100건 목표 (Premium 70 + Family 30)\n자평: 무상 교육 + CPA 보전 5%\n→ 종료 시 데이터 리뷰 → 본 계약 협의",
      color: C.gold,
    },
    {
      tag: "Phase 2", period: "3개월차~ · 본 운영", title: "본 가동",
      body: "상담사 15~20명 확대\n자문위원 풀 확대 (자평 영입, 3년 독점)\n갱신 콜 전담팀 분리\n월 가입 300~500건 목표",
      color: C.gold,
    },
    {
      tag: "Phase 3", period: "6개월차~ · 확장", title: "확장",
      body: "B2B(기업 임원 코칭) 세그먼트 — TM 채널 영업\n지역 독점 협의\n자평 광고 인입 → TM 클로징 협업\n연 매출 30억+ 시나리오",
      color: C.gold,
    },
  ];

  phases.forEach((p, i) => {
    const x = 0.6 + i * 4.15;
    const y = 2.0;
    const w = 3.95, h = 4.7;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color: C.surface }, line: { color: C.line, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.08,
      fill: { color: p.color }, line: { type: "none" },
    });
    s.addText(p.tag, {
      x: x + 0.3, y: y + 0.25, w: w - 0.6, h: 0.35,
      fontSize: 11, fontFace: F.serif, color: C.gold,
      charSpacing: 4, bold: true, margin: 0,
    });
    s.addText(p.period, {
      x: x + 0.3, y: y + 0.62, w: w - 0.6, h: 0.3,
      fontSize: 11, fontFace: F.sans, color: C.text2, margin: 0,
    });
    s.addText(p.title, {
      x: x + 0.3, y: y + 1.0, w: w - 0.6, h: 0.6,
      fontSize: 28, fontFace: F.serif, bold: true, color: C.text, margin: 0,
    });
    s.addShape(pres.shapes.LINE, {
      x: x + 0.3, y: y + 1.75, w: w - 0.6, h: 0,
      line: { color: C.line, width: 0.5 },
    });
    s.addText(p.body, {
      x: x + 0.3, y: y + 1.95, w: w - 0.6, h: h - 2.2,
      fontSize: 11, fontFace: F.sans, color: C.text2,
      paraSpaceAfter: 6, margin: 0,
    });
  });

  s.addText("검증  →  본 가동  →  확장", {
    x: 0.6, y: 6.85, w: W - 1.2, h: 0.4,
    fontSize: 12, fontFace: F.serif, color: C.gold,
    align: "center", charSpacing: 12, margin: 0,
  });
}

// ── 14. 다음 단계 ────────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addPageTitle(s, "이번 미팅 후 2주 내 결론 부탁드립니다", "進 · 다음 단계");
  addWatermark(s, 14);

  const steps = [
    { n: "1", t: "NDA 체결", when: "즉시", who: "양사" },
    { n: "2", t: "자평 데모 + 상품 디테일 추가 미팅", when: "1주 내", who: "자평 주관" },
    { n: "3", t: "파일럿 MoU 초안 교환", when: "1주 내", who: "자평 주관" },
    { n: "4", t: "상담사 5명 파일럿 시작", when: "합의 후 2주 내", who: "TM 주관" },
    { n: "5", t: "첫 30일 KPI 리뷰 (티어 믹스 포함)", when: "파일럿 30일차", who: "양사" },
    { n: "6", t: "본 계약 체결", when: "파일럿 후 2주 내", who: "양사" },
  ];

  steps.forEach((st, i) => {
    const y = 2.0 + i * 0.78;
    s.addShape(pres.shapes.OVAL, {
      x: 0.8, y: y + 0.05, w: 0.55, h: 0.55,
      fill: { color: C.gold }, line: { type: "none" },
    });
    s.addText(st.n, {
      x: 0.8, y: y + 0.05, w: 0.55, h: 0.55,
      fontSize: 18, fontFace: F.serif, bold: true, color: C.bg,
      align: "center", valign: "middle", margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.6, y, w: W - 2.2, h: 0.65,
      fill: { color: C.surface }, line: { color: C.line, width: 1 },
    });
    s.addText(st.t, {
      x: 1.85, y: y + 0.05, w: 6.5, h: 0.55,
      fontSize: 14, fontFace: F.serif, bold: true, color: C.text,
      valign: "middle", margin: 0,
    });
    s.addText(st.when, {
      x: 8.4, y: y + 0.05, w: 2.0, h: 0.55,
      fontSize: 12, fontFace: F.sans, color: C.gold,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(st.who, {
      x: 10.4, y: y + 0.05, w: 2.5, h: 0.55,
      fontSize: 11, fontFace: F.sans, color: C.text2,
      align: "center", valign: "middle", margin: 0,
    });
  });
}

// ── 15. 연락처 ───────────────────────────────────────────
{
  const s = pres.addSlide(); addBg(s);
  addWatermark(s, 15);

  s.addText([
    { text: "子", options: { color: C.text } },
    { text: "平", options: { color: C.gold } },
  ], {
    x: 0, y: 0.9, w: W, h: 1.4,
    fontSize: 110, fontFace: F.serif, bold: true,
    align: "center", margin: 0,
  });

  s.addText("결정 앞에, 자평.", {
    x: 0, y: 2.45, w: W, h: 0.6,
    fontSize: 28, fontFace: F.serif, bold: true, color: C.text,
    align: "center", margin: 0,
  });

  s.addText("900년 명리학 고전 위에서, AI와 사람이 함께 결정을 돕습니다.", {
    x: 0, y: 3.15, w: W, h: 0.4,
    fontSize: 13, fontFace: F.sans, color: C.text2,
    align: "center", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 2.5, y: 4.0, w: W - 5, h: 2.3,
    fill: { color: C.surface }, line: { color: C.gold, width: 2 },
  });
  s.addText("사업 제휴 문의", {
    x: 2.5, y: 4.2, w: W - 5, h: 0.4,
    fontSize: 11, fontFace: F.serif, color: C.gold,
    align: "center", charSpacing: 6, margin: 0,
  });
  s.addText("1577-0000", {
    x: 2.5, y: 4.65, w: W - 5, h: 0.8,
    fontSize: 38, fontFace: F.serif, bold: true, color: C.text,
    align: "center", margin: 0,
  });
  s.addText("partner@japyeong.kr  ·  평일 10–18시", {
    x: 2.5, y: 5.55, w: W - 5, h: 0.35,
    fontSize: 13, fontFace: F.sans, color: C.text2,
    align: "center", margin: 0,
  });
  s.addText("데모: https://ja-pyeong.vercel.app", {
    x: 2.5, y: 5.95, w: W - 5, h: 0.35,
    fontSize: 13, fontFace: F.sans, color: C.gold,
    align: "center", margin: 0,
  });

  s.addText("감사합니다.", {
    x: 0, y: 6.55, w: W, h: 0.5,
    fontSize: 18, fontFace: F.serif, color: C.text2,
    align: "center", charSpacing: 8, margin: 0,
  });
}

const OUT = "/Users/seungsoohan/Projects/JaPyeong/docs/sales/tm-partnership-pitch.pptx";
pres.writeFile({ fileName: OUT }).then(name => {
  console.log("SAVED:", name);
});

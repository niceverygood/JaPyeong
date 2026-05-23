"""LLM 다중 교차검증 — 엔진의 잠정 strength/geokguk/yongsin이
주요 LLM 합의 영역 안에 있는지 보조 신호로 측정.

⚠️ 이것은 자문위원 검증을 대체하지 않는다.
   LLM은 학습 데이터에 비전문 사주 사이트가 섞여 있어 '정답'이 아니다.
   본 도구는 "엔진 출력이 일반 통설 범위와 어긋나는가"의 사전 신호일 뿐.

사용처:
  - 서버: POST /api/_admin/cross-check (CROSSCHECK_SECRET 게이트)
  - CLI : python scripts/llm_crosscheck.py  (OPENROUTER_API_KEY 필요)
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from src.engine import geokguk as gk
from src.engine import strength as st
from src.engine import yongsin as ys
from src.engine.pillars import build_pillars
from src.engine.schema import BirthInfo

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# 다양성·비용 균형 — 4개 모델 (Anthropic/OpenAI/Google/Deepseek 계열).
# OpenRouter는 식별자를 종종 변경. 404 발생 시 환경변수 CROSSCHECK_MODELS(쉼표구분)로 오버라이드 가능.
DEFAULT_MODELS: tuple[str, ...] = (
    "anthropic/claude-sonnet-4",
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
    "deepseek/deepseek-chat",
)


def _resolve_models() -> tuple[str, ...]:
    override = os.environ.get("CROSSCHECK_MODELS", "").strip()
    if override:
        return tuple(m.strip() for m in override.split(",") if m.strip())
    return DEFAULT_MODELS

VALID_STRENGTH = {"신강", "신약", "중화"}
VALID_GEOKGUK = {
    "정관격", "편관격", "정재격", "편재격", "정인격", "편인격",
    "식신격", "상관격", "비견격", "겁재격",
}
VALID_YONGSIN = {"木", "火", "土", "金", "水"}

SYSTEM_PROMPT = """당신은 자평명리학에 익숙한 전문가입니다.
주어진 사주 8자에 대해 다음 세 항목만 JSON으로 답하세요. 다른 텍스트 금지.

{
  "strength": "신강|신약|중화",
  "geokguk": "정관격|편관격|정재격|편재격|정인격|편인격|식신격|상관격|비견격|겁재격",
  "yongsin": "木|火|土|金|水"
}

규칙:
- strength는 일간의 강약. 셋 중 하나.
- geokguk는 월지 지장간 투출 우선(통설). 위 10종 중 하나.
- yongsin은 억부 우선. 木·火·土·金·水 한 글자.
- 부연 설명·코드펜스 절대 금지. JSON만."""


def generate_seeded_cases(n: int = 20, seed: int = 42) -> list[BirthInfo]:
    """결정론적 합성 사주(검증케이스 아님). 1950~2010 분포."""
    r = random.Random(seed)
    out: list[BirthInfo] = []
    for _ in range(n):
        out.append(
            BirthInfo(
                gender=r.choice(["M", "F"]),
                calendar="solar",
                year=r.randint(1950, 2010),
                month=r.randint(1, 12),
                day=r.randint(1, 28),
                hour=r.randint(0, 23),
                minute=r.choice([0, 15, 30, 45]),
                longitude=126.9784,
                latitude=37.5665,
                timezone="Asia/Seoul",
            )
        )
    return out


@dataclass(frozen=True, slots=True)
class EngineLabels:
    strength: str
    geokguk: str
    yongsin: str
    pillars_str: str  # "乙丑 壬午 癸巳 己未"


@dataclass(frozen=True, slots=True)
class LlmAnswer:
    strength: str | None = None
    geokguk: str | None = None
    yongsin: str | None = None
    error: str | None = None


@dataclass
class CaseReport:
    case_id: str
    birth_summary: str
    engine: EngineLabels
    by_model: dict[str, LlmAnswer]
    agreement: dict[str, dict[str, bool]] = field(default_factory=dict)


@dataclass
class CrossCheckReport:
    cases: list[CaseReport]
    models: list[str]
    summary: dict[str, Any]


def _engine_evaluate(birth: BirthInfo) -> EngineLabels:
    p = build_pillars(birth)
    s = st.assess_strength(p)
    g = gk.determine_geokguk(p)
    y = ys.derive_yongsin(p)
    pillars_str = " ".join(
        f"{pil.gan}{pil.ji}" for pil in (p.year, p.month, p.day, p.hour) if pil is not None
    )
    return EngineLabels(
        strength=s.label,
        geokguk=g.name,
        yongsin=y.yongsin.value,
        pillars_str=pillars_str,
    )


def _build_user_prompt(engine: EngineLabels, birth: BirthInfo) -> str:
    return (
        f"사주 8자: {engine.pillars_str}\n"
        f"일간: {engine.pillars_str.split()[2][0]}\n"
        f"성별: {'남' if birth.gender == 'M' else '여'}\n"
        f"출생: {birth.year}-{birth.month:02d}-{birth.day:02d} "
        f"{birth.hour:02d}:{(birth.minute or 0):02d} (KST)\n\n"
        "위 사주에 대해 시스템 규칙대로 JSON만 답하세요."
    )


def _parse_llm_json(text: str) -> dict[str, Any]:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.endswith("```"):
            t = t[: -3]
    s, e = t.find("{"), t.rfind("}")
    if s != -1 and e != -1 and e > s:
        t = t[s : e + 1]
    return json.loads(t)


def _clean_label(value: str | None, valid: set[str]) -> str | None:
    if not isinstance(value, str):
        return None
    v = value.strip()
    if v in valid:
        return v
    # 일부 LLM이 "정관 격" / "정관(正官)격" 식으로 응답할 수 있으니 단순 정규화
    norm = re.sub(r"\s+", "", v)
    for c in valid:
        if c in norm or norm in c:
            return c
    return None


async def _call_one(client: httpx.AsyncClient, key: str, model: str, prompt: str) -> LlmAnswer:
    try:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ja-pyeong.vercel.app",
                "X-Title": "japyeong-crosscheck",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 200,
            },
            timeout=45.0,
        )
        if resp.status_code >= 400:
            return LlmAnswer(error=f"http {resp.status_code}: {resp.text[:120]}")
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        parsed = _parse_llm_json(text)
        return LlmAnswer(
            strength=_clean_label(parsed.get("strength"), VALID_STRENGTH),
            geokguk=_clean_label(parsed.get("geokguk"), VALID_GEOKGUK),
            yongsin=_clean_label(parsed.get("yongsin"), VALID_YONGSIN),
        )
    except Exception as e:
        return LlmAnswer(error=f"{type(e).__name__}: {e}")


async def run_crosscheck(
    cases: list[BirthInfo],
    models: tuple[str, ...] | None = None,
    api_key: str | None = None,
) -> CrossCheckReport:
    """모든 케이스 × 모든 모델 병렬 호출 후 합의 매트릭스 산출."""
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY 미설정")
    if models is None:
        models = _resolve_models()

    # 엔진 평가는 동기 (CPU)
    engine_labels = [_engine_evaluate(b) for b in cases]
    case_reports: list[CaseReport] = []

    async with httpx.AsyncClient() as client:
        for idx, (birth, eng) in enumerate(zip(cases, engine_labels, strict=True)):
            user_prompt = _build_user_prompt(eng, birth)
            results = await asyncio.gather(
                *(_call_one(client, key, m, user_prompt) for m in models),
                return_exceptions=False,
            )
            by_model = dict(zip(models, results, strict=True))
            agreement = {
                m: {
                    "strength": ans.strength == eng.strength,
                    "geokguk": ans.geokguk == eng.geokguk,
                    "yongsin": ans.yongsin == eng.yongsin,
                }
                for m, ans in by_model.items()
            }
            case_reports.append(
                CaseReport(
                    case_id=f"case_{idx + 1:02d}",
                    birth_summary=(
                        f"{birth.year}-{birth.month:02d}-{birth.day:02d} "
                        f"{birth.hour:02d}:{(birth.minute or 0):02d} "
                        f"({'남' if birth.gender == 'M' else '여'})"
                    ),
                    engine=eng,
                    by_model=by_model,
                    agreement=agreement,
                )
            )

    summary = _summarize(case_reports, models)
    return CrossCheckReport(cases=case_reports, models=list(models), summary=summary)


def _summarize(reports: list[CaseReport], models: tuple[str, ...]) -> dict[str, Any]:
    n = len(reports)
    if n == 0:
        return {"cases": 0}
    dims = ("strength", "geokguk", "yongsin")
    per_model: dict[str, dict[str, float]] = {}
    for m in models:
        agg = {d: 0 for d in dims}
        valid_n = {d: 0 for d in dims}
        for r in reports:
            ans = r.by_model[m]
            if ans.error:
                continue
            for d in dims:
                if getattr(ans, d) is not None:
                    valid_n[d] += 1
                    if r.agreement[m][d]:
                        agg[d] += 1
        per_model[m] = {
            d: (agg[d] / valid_n[d]) if valid_n[d] else 0.0 for d in dims
        }

    # 과반 일치(majority) — 모델 절반 이상이 엔진과 일치한 비율
    majority: dict[str, float] = {}
    for d in dims:
        wins = 0
        for r in reports:
            ok = sum(1 for m in models if r.agreement[m][d])
            if ok * 2 > len(models):
                wins += 1
        majority[d] = wins / n

    return {
        "cases": n,
        "models": list(models),
        "per_model_match_rate": per_model,
        "engine_vs_majority_match_rate": majority,
        "disclaimer": (
            "LLM 합의는 자문위원 검증을 대체하지 않습니다. "
            "통설 범위 안인지 확인하는 보조 신호일 뿐, 정통성 확정 아님."
        ),
    }


def report_to_dict(r: CrossCheckReport) -> dict[str, Any]:
    """JSON 직렬화용 (API 응답)."""
    return {
        "models": r.models,
        "summary": r.summary,
        "cases": [
            {
                "case_id": c.case_id,
                "birth": c.birth_summary,
                "pillars": c.engine.pillars_str,
                "engine": {
                    "strength": c.engine.strength,
                    "geokguk": c.engine.geokguk,
                    "yongsin": c.engine.yongsin,
                },
                "by_model": {
                    m: (
                        {"error": ans.error}
                        if ans.error
                        else {
                            "strength": ans.strength,
                            "geokguk": ans.geokguk,
                            "yongsin": ans.yongsin,
                        }
                    )
                    for m, ans in c.by_model.items()
                },
                "agreement": c.agreement,
            }
            for c in r.cases
        ],
    }

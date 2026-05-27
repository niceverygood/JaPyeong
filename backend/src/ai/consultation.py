"""Anthropic Claude 자문 호출 (v2 — 풍부한 응답 스키마).

3층 아키텍처(CLAUDE.md):
  Layer 1: 룰베이스 엔진 — 사주 JSON (saju_service.analyze_natal)
  Layer 2: LLM — 이 모듈 (학파 다양성·고전 인용·잠정 라벨 반영)
  Layer 3: 가드레일 — guardrails.filter_answer

ANTHROPIC_API_KEY 미설정 시 호출은 RuntimeError를 던진다(API 핸들러가 503으로 변환).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import anthropic

from src.ai.prompts import (
    COMPAT_SYSTEM_PROMPT,
    DECISION_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_compat_user_message,
    build_decision_user_message,
    build_user_message,
)

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL_STANDARD", "claude-sonnet-4-5")
MAX_TOKENS = 2200  # v2: contested/cautions 다 채우면 길어지므로 여유. 잘림 = JSON 파싱 실패 502
TEMPERATURE = 0.5
RETRY_ON_PARSE_FAIL = 1  # Claude가 가끔 JSON을 끊기게 생성 → 1회 자동 재시도


@dataclass(frozen=True, slots=True)
class Citation:
    source: str
    volume: str | None = None


@dataclass(frozen=True, slots=True)
class ConsultationResult:
    answer: str
    basis: str
    perspective: str  # v2: 사주에서 관찰되는 큰 흐름·관점
    timing: str  # v2: 시기 코멘트 (없으면 빈 문자열)
    cautions: tuple[str, ...]  # v2: 주의 신호 0~3개
    citations: tuple[Citation, ...]
    contested: tuple[str, ...]  # v2: 학파별 견해 차이 0~3개
    confidence: str  # v2: "high" | "medium" | "low"
    follow_up_suggestions: tuple[str, ...]
    model: str


_VALID_CONFIDENCE = {"high", "medium", "low"}


def _client() -> anthropic.Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY 미설정 — Vercel 환경변수에 키를 추가하세요.")
    return anthropic.Anthropic(api_key=key)


def consult(natal: dict, question: str, model: str | None = None) -> ConsultationResult:
    """룰베이스 사주 JSON + 질문 → Claude 자문(JSON) 호출.

    Claude가 가끔 max_tokens 한계로 JSON을 끊기게 생성 → 파싱 실패 시 1회 재시도.
    """
    natal_json = json.dumps(natal, ensure_ascii=False, default=str)
    msg = build_user_message(natal_json, question)
    mdl = model or DEFAULT_MODEL
    client = _client()

    data: dict | None = None
    last_err: Exception | None = None
    for _ in range(RETRY_ON_PARSE_FAIL + 1):
        resp = client.messages.create(
            model=mdl,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": msg}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        try:
            data = _parse_json_lenient(text)
            break
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e  # 파싱 실패 → 재시도
            continue
    if data is None:
        raise RuntimeError(
            f"Claude JSON 파싱 실패({RETRY_ON_PARSE_FAIL + 1}회): {last_err}"
        )

    citations = tuple(
        Citation(source=c.get("source", "").strip(), volume=(c.get("volume") or None))
        for c in (data.get("citations") or [])
        if isinstance(c, dict) and c.get("source")
    )
    cautions = tuple(
        str(s).strip() for s in (data.get("cautions") or []) if str(s).strip()
    )[:3]
    contested = tuple(
        str(s).strip() for s in (data.get("contested") or []) if str(s).strip()
    )[:3]
    confidence = str(data.get("confidence", "medium")).strip().lower()
    if confidence not in _VALID_CONFIDENCE:
        confidence = "medium"

    return ConsultationResult(
        answer=str(data.get("answer", "")).strip(),
        basis=str(data.get("basis", "")).strip(),
        perspective=str(data.get("perspective", "")).strip(),
        timing=str(data.get("timing", "")).strip(),
        cautions=cautions,
        citations=citations,
        contested=contested,
        confidence=confidence,
        follow_up_suggestions=tuple(
            str(s).strip() for s in (data.get("follow_up_suggestions") or []) if str(s).strip()
        )[:3],
        model=mdl,
    )


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """결정 도우미 A/B 응답."""

    option_a_view: str
    option_b_view: str
    comparison: str
    lean: str  # "A" | "B" | "balanced"
    lean_reason: str
    answer: str
    basis: str
    perspective: str
    timing: str
    cautions: tuple[str, ...]
    citations: tuple[Citation, ...]
    contested: tuple[str, ...]
    confidence: str
    follow_up_suggestions: tuple[str, ...]
    model: str


_VALID_LEAN = {"A", "B", "balanced"}


def consult_decision(
    natal: dict,
    option_a_title: str,
    option_a_desc: str,
    option_b_title: str,
    option_b_desc: str,
    context: str | None = None,
    model: str | None = None,
) -> DecisionResult:
    """사주 + 두 선택지 → Claude 결정 도우미 자문."""
    natal_json = json.dumps(natal, ensure_ascii=False, default=str)
    msg = build_decision_user_message(
        natal_json=natal_json,
        option_a_title=option_a_title,
        option_a_desc=option_a_desc,
        option_b_title=option_b_title,
        option_b_desc=option_b_desc,
        context=context,
    )
    mdl = model or DEFAULT_MODEL
    client = _client()

    data: dict | None = None
    last_err: Exception | None = None
    for _ in range(RETRY_ON_PARSE_FAIL + 1):
        resp = client.messages.create(
            model=mdl,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=DECISION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": msg}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        try:
            data = _parse_json_lenient(text)
            break
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            continue
    if data is None:
        raise RuntimeError(
            f"Claude 결정 JSON 파싱 실패({RETRY_ON_PARSE_FAIL + 1}회): {last_err}"
        )

    citations = tuple(
        Citation(source=c.get("source", "").strip(), volume=(c.get("volume") or None))
        for c in (data.get("citations") or [])
        if isinstance(c, dict) and c.get("source")
    )
    cautions = tuple(
        str(s).strip() for s in (data.get("cautions") or []) if str(s).strip()
    )[:3]
    contested = tuple(
        str(s).strip() for s in (data.get("contested") or []) if str(s).strip()
    )[:3]
    confidence = str(data.get("confidence", "medium")).strip().lower()
    if confidence not in _VALID_CONFIDENCE:
        confidence = "medium"
    lean = str(data.get("lean", "balanced")).strip()
    if lean not in _VALID_LEAN:
        lean = "balanced"

    return DecisionResult(
        option_a_view=str(data.get("option_a_view", "")).strip(),
        option_b_view=str(data.get("option_b_view", "")).strip(),
        comparison=str(data.get("comparison", "")).strip(),
        lean=lean,
        lean_reason=str(data.get("lean_reason", "")).strip(),
        answer=str(data.get("answer", "")).strip(),
        basis=str(data.get("basis", "")).strip(),
        perspective=str(data.get("perspective", "")).strip(),
        timing=str(data.get("timing", "")).strip(),
        cautions=cautions,
        citations=citations,
        contested=contested,
        confidence=confidence,
        follow_up_suggestions=tuple(
            str(s).strip() for s in (data.get("follow_up_suggestions") or []) if str(s).strip()
        )[:3],
        model=mdl,
    )


def consult_compatibility(
    natal_a: dict,
    natal_b: dict,
    analysis: dict,
    relationship_type: str,
    label_a: str | None = None,
    label_b: str | None = None,
    question: str | None = None,
    model: str | None = None,
) -> ConsultationResult:
    """두 사주 + 결정론적 분석 → Claude 궁합 자문 호출.

    응답 스키마는 일반 consult()와 동일(ConsultationResult).
    """
    natal_a_json = json.dumps(natal_a, ensure_ascii=False, default=str)
    natal_b_json = json.dumps(natal_b, ensure_ascii=False, default=str)
    analysis_json = json.dumps(analysis, ensure_ascii=False, default=str)
    msg = build_compat_user_message(
        natal_a_json=natal_a_json,
        natal_b_json=natal_b_json,
        analysis_json=analysis_json,
        relationship_type=relationship_type,
        label_a=label_a,
        label_b=label_b,
        question=question,
    )
    mdl = model or DEFAULT_MODEL
    client = _client()

    data: dict | None = None
    last_err: Exception | None = None
    for _ in range(RETRY_ON_PARSE_FAIL + 1):
        resp = client.messages.create(
            model=mdl,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=COMPAT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": msg}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        try:
            data = _parse_json_lenient(text)
            break
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            continue
    if data is None:
        raise RuntimeError(
            f"Claude 궁합 JSON 파싱 실패({RETRY_ON_PARSE_FAIL + 1}회): {last_err}"
        )

    citations = tuple(
        Citation(source=c.get("source", "").strip(), volume=(c.get("volume") or None))
        for c in (data.get("citations") or [])
        if isinstance(c, dict) and c.get("source")
    )
    cautions = tuple(
        str(s).strip() for s in (data.get("cautions") or []) if str(s).strip()
    )[:3]
    contested = tuple(
        str(s).strip() for s in (data.get("contested") or []) if str(s).strip()
    )[:3]
    confidence = str(data.get("confidence", "medium")).strip().lower()
    if confidence not in _VALID_CONFIDENCE:
        confidence = "medium"

    return ConsultationResult(
        answer=str(data.get("answer", "")).strip(),
        basis=str(data.get("basis", "")).strip(),
        perspective=str(data.get("perspective", "")).strip(),
        timing=str(data.get("timing", "")).strip(),
        cautions=cautions,
        citations=citations,
        contested=contested,
        confidence=confidence,
        follow_up_suggestions=tuple(
            str(s).strip() for s in (data.get("follow_up_suggestions") or []) if str(s).strip()
        )[:3],
        model=mdl,
    )


def _parse_json_lenient(text: str) -> dict:
    """JSON 코드펜스/잡설을 관용적으로 떼고 파싱."""
    t = text.strip()
    if t.startswith("```"):
        # ```json ... ``` or ``` ... ```
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.endswith("```"):
            t = t[: -3]
    # 가장 바깥 { ... } 슬라이스
    s, e = t.find("{"), t.rfind("}")
    if s != -1 and e != -1 and e > s:
        t = t[s : e + 1]
    return json.loads(t)

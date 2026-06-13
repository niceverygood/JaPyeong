"""/v1/decision 라우터 — 사주 + 두 선택지 → LLM 결정 도우미 자문."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from src.ai import consultation, guardrails
from src.ai.glossary import annotate_hanja
from src.ai.tone_down import tone_down
from src.api.v1.chat_schemas import CitationDTO
from src.api.v1.decision_schemas import DecisionRequest, DecisionResponse
from src.middleware.rate_limit import get_limiter, resolve_tier, resolve_user_id
from src.services import decision_log_service, saju_service

router = APIRouter(prefix="/v1/decision", tags=["decision"])


def _post(text: str) -> str:
    """단정 톤다운 + 한자 자동 병기."""
    return annotate_hanja(tone_down(text))


@router.post("", response_model=DecisionResponse)
async def decision(req: DecisionRequest, request: Request) -> DecisionResponse:
    tier = resolve_tier(request)
    await get_limiter().enforce(request, user_tier=tier)
    # 0. 위기 키워드 (context + 두 옵션 description 검사)
    blob = " ".join(
        s
        for s in (
            req.context or "",
            req.option_a.title,
            req.option_a.description,
            req.option_b.title,
            req.option_b.description,
        )
        if s
    )
    pre = guardrails.check_question(blob)
    if not pre.safe:
        return DecisionResponse(
            option_a_view="",
            option_b_view="",
            comparison="",
            lean="balanced",
            lean_reason="안전 안내",
            answer=pre.answer,
            basis="안전 안내",
            confidence="high",
            flags=list(pre.flags),
            model="(guardrail)",
        )

    # 1. 룰베이스 원국
    try:
        natal = saju_service.analyze_natal(req.birth).model_dump()
    except NotImplementedError as e:
        raise HTTPException(422, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    # 2. LLM 자문
    try:
        result = consultation.consult_decision(
            natal=natal,
            option_a_title=req.option_a.title,
            option_a_desc=req.option_a.description,
            option_b_title=req.option_b.title,
            option_b_desc=req.option_b.description,
            context=req.context,
            user_tier=tier,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"결정 자문 호출 실패: {e}") from e

    # 3. 후처리 가드레일 (answer 위주)
    post = guardrails.filter_answer(result.answer)

    # 3-1. 결정 로그 자산화 (DATABASE_URL 설정 시만 작동, 진짜 해자 ❶)
    # JWT 가 있으면 회원 결정으로 적립 → 사후 만족도 추적·프롬프트 보강의 복리 데이터.
    try:
        await decision_log_service.save_decision_log(
            user_id=resolve_user_id(request),  # 비로그인은 None (기존 동작 유지)
            birth_record_id=None,
            decision_type="general",  # Sprint 11-12 자동 분류기
            natal=natal,
            option_a_summary=req.option_a.title,
            option_b_summary=req.option_b.title,
            user_context=req.context,
            lean=result.lean,
            advisor_response_summary=result.answer[:500],
            confidence=result.confidence,
        )
    except Exception:
        # 결정 로그 실패가 자문 응답을 막아선 안 됨
        pass

    # 4. 한자 자동 병기
    return DecisionResponse(
        option_a_view=_post(result.option_a_view),
        option_b_view=_post(result.option_b_view),
        comparison=_post(result.comparison),
        lean=result.lean,  # type: ignore[arg-type]
        lean_reason=_post(result.lean_reason),
        answer=_post(post.answer),
        basis=_post(result.basis),
        perspective=_post(result.perspective),
        timing=_post(result.timing),
        cautions=[_post(c) for c in result.cautions],
        citations=[
            CitationDTO(
                source=_post(c.source),
                volume=_post(c.volume) if c.volume else None,
            )
            for c in result.citations
        ],
        contested=[_post(c) for c in result.contested],
        confidence=result.confidence,
        follow_up_suggestions=[_post(s) for s in result.follow_up_suggestions],
        flags=list(post.flags),
        model=result.model,
    )

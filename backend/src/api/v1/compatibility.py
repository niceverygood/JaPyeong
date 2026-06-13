"""/v1/compatibility 라우터 — 두 사주 결정론 + LLM 궁합 자문 + 가드레일.

3층 분리: compatibility_service(엔진) → consultation.consult_compatibility(LLM) → guardrails.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from src.ai import consultation, guardrails
from src.ai.glossary import annotate_hanja
from src.ai.tone_down import tone_down
from src.api.v1.chat_schemas import CitationDTO
from src.api.v1.compat_schemas import CompatRequest, CompatResponse
from src.middleware.rate_limit import get_limiter, resolve_tier
from src.services import compatibility_service

router = APIRouter(prefix="/v1/compatibility", tags=["compatibility"])


def _post(text: str) -> str:
    """단정 톤다운 + 한자 자동 병기."""
    return annotate_hanja(tone_down(text))


@router.post("", response_model=CompatResponse)
async def compatibility(req: CompatRequest, request: Request) -> CompatResponse:
    tier = resolve_tier(request)
    await get_limiter().enforce(request, user_tier=tier)
    # 0. 위기 키워드 단축 (질문이 있을 때만)
    if req.question:
        pre = guardrails.check_question(req.question)
        if not pre.safe:
            empty_analysis = _empty_analysis()
            return CompatResponse(
                analysis=empty_analysis,
                answer=pre.answer,
                basis="안전 안내",
                confidence="high",
                flags=list(pre.flags),
                model="(guardrail)",
                relationship_type=req.relationship_type,
            )

    # 1. 결정론 — 두 사주 8자 + cross 분석
    try:
        pa, pb, analysis = compatibility_service.analyze_pair(req.birth_a, req.birth_b)
    except NotImplementedError as e:
        raise HTTPException(422, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    # 2. LLM 자문
    try:
        result = consultation.consult_compatibility(
            natal_a={"pillars": pa.model_dump()},
            natal_b={"pillars": pb.model_dump()},
            analysis=analysis.model_dump(),
            relationship_type=req.relationship_type,
            label_a=req.label_a,
            label_b=req.label_b,
            question=req.question,
            user_tier=tier,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"궁합 자문 호출 실패: {e}") from e

    # 3. 후처리 가드레일
    post = guardrails.filter_answer(result.answer)

    # 4. 한자 자동 병기
    return CompatResponse(
        analysis=analysis,
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
        relationship_type=req.relationship_type,
    )


def _empty_analysis():
    """위기 가드레일 단축 시 사용할 placeholder analysis."""
    from src.api.v1.compat_schemas import (
        CompatAnalysisDTO,
        DayMasterPairDTO,
        ElementCombinedDTO,
    )

    return CompatAnalysisDTO(
        cross_relations=[],
        day_master_pair=DayMasterPairDTO(
            day_master_a="-",
            day_master_b="-",
            element_a="-",
            element_b="-",
            a_to_b="-",
            b_to_a="-",
            dynamic="-",
        ),
        element_combined=ElementCombinedDTO(
            mok=0,
            hwa=0,
            to=0,
            geum=0,
            su=0,
            total=0,
            balance_a=0,
            balance_b=0,
            balance_combined=0,
            balance_gain=0,
        ),
        strong_bonds_count=0,
        conflicts_count=0,
        notes=[],
    )

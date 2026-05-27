"""/v1/decision 라우터 — 사주 + 두 선택지 → LLM 결정 도우미 자문."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.ai import consultation, guardrails
from src.ai.glossary import annotate_hanja
from src.api.v1.chat_schemas import CitationDTO
from src.api.v1.decision_schemas import DecisionRequest, DecisionResponse
from src.services import saju_service

router = APIRouter(prefix="/v1/decision", tags=["decision"])


@router.post("", response_model=DecisionResponse)
async def decision(req: DecisionRequest) -> DecisionResponse:
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
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"결정 자문 호출 실패: {e}") from e

    # 3. 후처리 가드레일 (answer 위주)
    post = guardrails.filter_answer(result.answer)

    # 4. 한자 자동 병기
    return DecisionResponse(
        option_a_view=annotate_hanja(result.option_a_view),
        option_b_view=annotate_hanja(result.option_b_view),
        comparison=annotate_hanja(result.comparison),
        lean=result.lean,  # type: ignore[arg-type]
        lean_reason=annotate_hanja(result.lean_reason),
        answer=annotate_hanja(post.answer),
        basis=annotate_hanja(result.basis),
        perspective=annotate_hanja(result.perspective),
        timing=annotate_hanja(result.timing),
        cautions=[annotate_hanja(c) for c in result.cautions],
        citations=[
            CitationDTO(
                source=annotate_hanja(c.source),
                volume=annotate_hanja(c.volume) if c.volume else None,
            )
            for c in result.citations
        ],
        contested=[annotate_hanja(c) for c in result.contested],
        confidence=result.confidence,
        follow_up_suggestions=[annotate_hanja(s) for s in result.follow_up_suggestions],
        flags=list(post.flags),
        model=result.model,
    )

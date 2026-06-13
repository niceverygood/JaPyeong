"""/v1/timing 라우터 — 결정 타이밍 코치(시그니처).

3층 분리: timing_service(결정론 택일 스캔) → consultation.consult_timing(LLM 코치)
→ guardrails. 결정론 캘린더·길일은 항상 반환하고, LLM 내러티브는 best-effort.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from src.ai import consultation, guardrails
from src.ai.glossary import annotate_hanja
from src.ai.tone_down import tone_down
from src.api.v1.chat_schemas import CitationDTO
from src.api.v1.date_schemas import CandidateDateDTO
from src.api.v1.timing_schemas import TimingRequest, TimingResponse
from src.middleware.rate_limit import get_limiter, resolve_user_id
from src.services import timing_service
from src.services.user_service import get_user_tier

router = APIRouter(prefix="/v1/timing", tags=["timing"])


def _post(text: str) -> str:
    """단정 톤다운 + 한자 자동 병기."""
    return annotate_hanja(tone_down(text))


def _dto(c) -> CandidateDateDTO:  # noqa: ANN001
    return CandidateDateDTO(
        date=c.date,
        day_pillar=c.day_pillar,
        score=c.score,
        label=c.label,
        ten_god=c.ten_god,
        reasons=list(c.reasons),
    )


@router.post("", response_model=TimingResponse)
async def timing(req: TimingRequest, request: Request) -> TimingResponse:
    # 권한은 DB 활성구독 기준(클레임 미신뢰) + 티어별 한도/심층모델
    tier = await get_user_tier(resolve_user_id(request))
    await get_limiter().enforce(request, user_tier=tier)

    # 1. 결정론 — 기간 스캔 + 길일/피할날 랭킹
    try:
        result = timing_service.analyze_timing(
            birth=req.birth,
            event_type=req.event_type,
            start=req.start,
            end=req.end,
            top_n=req.top_n,
        )
    except NotImplementedError as e:
        raise HTTPException(422, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    calendar = [_dto(c) for c in result.calendar]
    best = [_dto(c) for c in result.best]
    avoid = [_dto(c) for c in result.avoid]

    # 2. LLM 코치 내러티브 — best-effort (실패해도 캘린더/길일은 반환)
    narrative: dict = {
        "recommendation": "",
        "perspective": "",
        "timing": "",
        "cautions": [],
        "citations": [],
        "contested": [],
        "confidence": "medium",
        "model": "",
    }
    try:
        narr = consultation.consult_timing(
            natal={"pillars": result.natal.model_dump()},
            event_type=result.event_type,
            span_days=(result.end - result.start).days,
            best_summary=timing_service.summarize_for_llm(result.best),
            avoid_summary=timing_service.summarize_for_llm(result.avoid),
            user_tier=tier,
        )
        post = guardrails.filter_answer(narr.answer)
        narrative = {
            "recommendation": _post(post.answer),
            "perspective": _post(narr.perspective),
            "timing": _post(narr.timing),
            "cautions": [_post(c) for c in narr.cautions],
            "citations": [
                CitationDTO(
                    source=_post(c.source),
                    volume=_post(c.volume) if c.volume else None,
                )
                for c in narr.citations
            ],
            "contested": [_post(c) for c in narr.contested],
            "confidence": narr.confidence,
            "model": narr.model,
        }
    except Exception:  # noqa: BLE001 — 내러티브 실패는 치명적 아님
        pass

    return TimingResponse(
        event_type=result.event_type,
        start=result.start,
        end=result.end,
        calendar=calendar,
        best=best,
        avoid=avoid,
        **narrative,
    )

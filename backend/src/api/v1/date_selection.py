"""/v1/date-selection 라우터 — 사용자 사주 대비 좋은 날 찾기."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.v1.date_schemas import (
    CandidateDateDTO,
    DateSelectionRequest,
    DateSelectionResponse,
)
from src.engine import date_selection as ds
from src.engine.pillars import build_pillars

router = APIRouter(prefix="/v1/date-selection", tags=["date-selection"])


@router.post("", response_model=DateSelectionResponse)
async def date_selection(req: DateSelectionRequest) -> DateSelectionResponse:
    try:
        natal = build_pillars(req.birth)
    except NotImplementedError as e:
        raise HTTPException(422, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    try:
        candidates = ds.select_dates(
            natal=natal,
            start=req.start,
            end=req.end,
            event_type=req.event_type,
            top_n=req.top_n,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    return DateSelectionResponse(
        event_type=req.event_type,
        start=req.start,
        end=req.end,
        candidates=[
            CandidateDateDTO(
                date=c.date,
                day_pillar=c.day_pillar,
                score=c.score,
                label=c.label,
                ten_god=c.ten_god,
                reasons=list(c.reasons),
            )
            for c in candidates
        ],
    )

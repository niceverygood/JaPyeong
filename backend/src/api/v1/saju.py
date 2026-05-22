"""/v1/saju 라우터 — 원국 분석·흐르는 운 조회.

Phase 2: 룰베이스 엔진 결과만 노출(LLM 자문은 Phase 4).
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from src.api.v1.saju_schemas import LuckResponse, NatalResponse
from src.engine.schema import BirthInfo
from src.services import saju_service

router = APIRouter(prefix="/v1/saju", tags=["saju"])


@router.post("/analyze", response_model=NatalResponse)
async def analyze(birth: BirthInfo) -> NatalResponse:
    """출생 정보 → 원국(8자)·십성·오행·합충형해파·대운."""
    try:
        return saju_service.analyze_natal(birth)
    except NotImplementedError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/luck", response_model=LuckResponse)
async def luck(
    on: Annotated[
        date | None, Query(description="조회 일자(YYYY-MM-DD). 미지정 시 오늘")
    ] = None,
) -> LuckResponse:
    """특정 일자의 세운·월운·일운."""
    return saju_service.luck_for(on or date.today())

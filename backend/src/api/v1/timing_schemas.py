"""/v1/timing API DTO — 결정 타이밍 코치(시그니처)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from src.api.v1.chat_schemas import CitationDTO
from src.api.v1.date_schemas import CandidateDateDTO
from src.engine.schema import BirthInfo

EventType = Literal["marriage", "moving", "business", "contract", "general"]


class TimingRequest(BaseModel):
    birth: BirthInfo
    start: date
    end: date
    event_type: EventType = "general"
    top_n: int = Field(default=5, ge=1, le=15)


class TimingResponse(BaseModel):
    event_type: EventType
    start: date
    end: date
    # 캘린더 히트맵용 전체 일자 (날짜 오름차순)
    calendar: list[CandidateDateDTO]
    # 추천 길일 / 피할 날
    best: list[CandidateDateDTO]
    avoid: list[CandidateDateDTO]
    # LLM 코치 내러티브 (실패 시 빈 문자열 — 캘린더는 항상 제공)
    recommendation: str = ""
    perspective: str = ""
    timing: str = ""
    cautions: list[str] = []
    citations: list[CitationDTO] = []
    contested: list[str] = []
    confidence: str = "medium"
    model: str = ""
    note: str = (
        "잠정 — 본 결과는 자평 결정론 엔진(천간·지지·십성·합충)만 사용합니다. "
        "전통 택일의 신살(천을귀인·황도흑도 등)은 자문위원 정책 확정 후 반영 예정입니다."
    )

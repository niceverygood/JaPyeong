"""/v1/date-selection API DTO."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from src.engine.schema import BirthInfo, Pillar

EventType = Literal["marriage", "moving", "business", "contract", "general"]


class DateSelectionRequest(BaseModel):
    birth: BirthInfo
    start: date
    end: date
    event_type: EventType = "general"
    top_n: int = Field(default=5, ge=1, le=30)


class CandidateDateDTO(BaseModel):
    date: date
    day_pillar: Pillar
    score: float
    label: str  # 대길/길/평/주의/흉
    ten_god: str  # 한글
    reasons: list[str]


class DateSelectionResponse(BaseModel):
    event_type: EventType
    start: date
    end: date
    candidates: list[CandidateDateDTO]
    note: str = (
        "잠정 — 본 결과는 자평 결정론 엔진(천간·지지·십성)만 사용합니다. "
        "전통 택일의 신살(천을귀인·황도흑도 등)은 자문위원 정책 확정 후 반영 예정입니다."
    )

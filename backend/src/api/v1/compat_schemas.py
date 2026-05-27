"""/v1/compatibility API 요청·응답 DTO."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.api.v1.chat_schemas import CitationDTO
from src.api.v1.saju_schemas import RelationResponse
from src.engine.schema import BirthInfo

RelationshipType = Literal["romantic", "marriage", "business", "family", "general"]


class CompatRequest(BaseModel):
    """두 사람의 출생정보 + 관계 유형 + (선택) 추가 질문."""

    birth_a: BirthInfo
    birth_b: BirthInfo
    relationship_type: RelationshipType = "romantic"
    question: str | None = Field(default=None, max_length=2000)
    # 선택: 사용자 친화적 라벨 (LLM이 답변에 반영)
    label_a: str | None = Field(default=None, max_length=40)
    label_b: str | None = Field(default=None, max_length=40)


class DayMasterPairDTO(BaseModel):
    day_master_a: str  # 한자 천간 (예: 丙)
    day_master_b: str
    element_a: str  # 오행 한자 (木/火/...)
    element_b: str
    a_to_b: str  # 십성 한글 (예: 정관)
    b_to_a: str
    dynamic: str  # 비화/A생B/B생A/A극B/B극A


class ElementCombinedDTO(BaseModel):
    mok: float
    hwa: float
    to: float
    geum: float
    su: float
    total: float
    balance_a: float
    balance_b: float
    balance_combined: float
    balance_gain: float


class CompatAnalysisDTO(BaseModel):
    """결정론적 궁합 분석 결과 (UI 표시·LLM 입력 공통)."""

    cross_relations: list[RelationResponse]
    day_master_pair: DayMasterPairDTO
    element_combined: ElementCombinedDTO
    strong_bonds_count: int
    conflicts_count: int
    notes: list[str]


class CompatResponse(BaseModel):
    """v1 궁합 응답 — 결정론적 분석 + LLM 자문."""

    # 결정론적
    analysis: CompatAnalysisDTO
    # LLM 자문
    answer: str
    basis: str
    perspective: str = ""
    timing: str = ""
    cautions: list[str] = []
    citations: list[CitationDTO] = []
    contested: list[str] = []
    confidence: str = "medium"
    follow_up_suggestions: list[str] = []
    flags: list[str] = []
    model: str
    relationship_type: RelationshipType

"""/v1/chat API 요청·응답 DTO."""

from pydantic import BaseModel, Field

from src.engine.schema import BirthInfo


class ChatRequest(BaseModel):
    birth: BirthInfo
    question: str = Field(min_length=1, max_length=2000)


class CitationDTO(BaseModel):
    source: str
    volume: str | None = None


class ChatResponse(BaseModel):
    answer: str
    basis: str
    citations: list[CitationDTO]
    follow_up_suggestions: list[str]
    flags: list[str]  # 가드레일 플래그 (medical_legal / absolute_phrasing / crisis_*)
    model: str

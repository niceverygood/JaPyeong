"""/v1/chat API 요청·응답 DTO (v2: 학설 다양성 반영)."""

from pydantic import BaseModel, Field

from src.engine.schema import BirthInfo


class ChatRequest(BaseModel):
    birth: BirthInfo
    question: str = Field(min_length=1, max_length=2000)


class CitationDTO(BaseModel):
    source: str
    volume: str | None = None


class ChatResponse(BaseModel):
    """v2: perspective/timing/cautions/contested/confidence 추가."""

    answer: str
    basis: str
    perspective: str = ""
    timing: str = ""
    cautions: list[str] = []
    citations: list[CitationDTO] = []
    contested: list[str] = []  # 학파별 견해 차이
    confidence: str = "medium"  # high | medium | low
    follow_up_suggestions: list[str] = []
    flags: list[str] = []  # 가드레일 플래그
    model: str
    daily_remaining: int | None = None  # 오늘 남은 무료 자문 횟수(전환 UI)
    daily_limit: int | None = None  # 티어별 일일 한도

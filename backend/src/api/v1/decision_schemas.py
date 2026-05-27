"""/v1/decision API DTO — 결정 도우미 A/B."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.api.v1.chat_schemas import CitationDTO
from src.engine.schema import BirthInfo

Lean = Literal["A", "B", "balanced"]


class OptionInput(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=600)


class DecisionRequest(BaseModel):
    birth: BirthInfo
    option_a: OptionInput
    option_b: OptionInput
    context: str | None = Field(default=None, max_length=1500)


class DecisionResponse(BaseModel):
    option_a_view: str
    option_b_view: str
    comparison: str
    lean: Lean
    lean_reason: str
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

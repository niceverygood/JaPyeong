"""AI 자문 후처리 가드레일.

CLAUDE.md "[Layer 3] 후처리 가드레일" 사양:
  - 단정 패턴 차단
  - 의학·법률 단정 차단
  - 자살·자해 키워드 → 상담 안내
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 자살·자해·폭력 키워드 (감지 시 상담 자원 안내 우선)
CRISIS_KEYWORDS = (
    "자살", "자해", "죽고싶", "죽고 싶", "목숨을 끊", "스스로 목숨", "자진",
)

# 단정형 패턴 (자문 톤 위반)
ABSOLUTE_PATTERNS = (
    r"반드시\s*[가-힣]",
    r"무조건\s*[가-힣]",
    r"확실히\s*\S*\s*(됩니다|일어납니다)",
    r"틀림없이",
)

# 의학·법률 단정 (전문가 상담 권유로 대체 권고)
MEDICAL_LEGAL = ("진단", "처방", "수술", "투약", "법적 효력", "고소하세요", "이혼하세요")

CRISIS_NOTICE = (
    "[안내] 위급한 생각이 든다면 자살예방상담전화 109(24시간) 또는 정신건강 위기상담 "
    "1577-0199(24시간)로 연락해 주세요. 사주 자문은 위기 상담을 대체하지 않습니다."
)


@dataclass(frozen=True, slots=True)
class GuardrailReport:
    """가드레일 처리 결과."""

    safe: bool
    answer: str
    flags: tuple[str, ...]


def check_question(question: str) -> GuardrailReport:
    """사용자 질문 사전 검사. 위기 키워드면 즉시 상담 안내로 답을 대체."""
    if _has_any(question, CRISIS_KEYWORDS):
        return GuardrailReport(safe=False, answer=CRISIS_NOTICE, flags=("crisis_input",))
    return GuardrailReport(safe=True, answer="", flags=())


def filter_answer(answer: str) -> GuardrailReport:
    """LLM 답변 후처리. 위기/단정/의학단정 검사 + 마일드 완화."""
    flags: list[str] = []

    if _has_any(answer, CRISIS_KEYWORDS):
        return GuardrailReport(
            safe=False, answer=CRISIS_NOTICE, flags=("crisis_output",)
        )

    if _has_any(answer, MEDICAL_LEGAL):
        flags.append("medical_legal")
        answer = (
            answer.rstrip()
            + "\n\n※ 의학·법률 사안은 사주 자문이 아닌 해당 분야 전문가의 상담을 권합니다."
        )

    for pat in ABSOLUTE_PATTERNS:
        if re.search(pat, answer):
            flags.append("absolute_phrasing")
            break  # 단일 플래그로 충분

    return GuardrailReport(safe=True, answer=answer, flags=tuple(flags))


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    t = text or ""
    return any(n in t for n in needles)

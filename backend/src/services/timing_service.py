"""결정 타이밍 코치 — 명식 대비 기간 내 길흉 캘린더 + 길일/피할날 랭킹.

자평 시그니처 기능. date_selection.score_date 를 일 단위로 스캔해
  (a) calendar — 캘린더 히트맵용 전체 일자 점수,
  (b) best    — 추천 길일(점수 내림차순),
  (c) avoid   — 피해야 할 날(점수 오름차순)
을 산출한다. LLM 코치 내러티브(consultation.consult_timing)는 라우터가 별도 호출하며,
이 서비스는 순수·결정론적이다(테스트·재현 용이).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from src.engine import date_selection as ds
from src.engine.pillars import build_pillars
from src.engine.schema import BirthInfo, FourPillars

# 캘린더 히트맵 payload 상한 — 약 3개월. 그 이상은 ValueError.
MAX_CALENDAR_DAYS = 92

EventType = str  # marriage | moving | business | contract | general


@dataclass(frozen=True, slots=True)
class TimingResult:
    event_type: EventType
    start: date
    end: date
    natal: FourPillars
    calendar: list[ds.CandidateDate]  # 기간 내 전체 일자 (날짜 오름차순)
    best: list[ds.CandidateDate]       # 추천 길일 (점수 내림차순)
    avoid: list[ds.CandidateDate]      # 피할 날 (점수 오름차순)


def analyze_timing(
    birth: BirthInfo,
    event_type: EventType,
    start: date,
    end: date,
    top_n: int = 5,
) -> TimingResult:
    """기간 내 일자를 명식 대비 점수화하고 길일/피할날을 랭킹한다.

    Raises:
        ValueError: 기간 역전 / 상한(92일) 초과 / 입력 오류
        NotImplementedError: 엔진 미구현 경로
    """
    if end < start:
        raise ValueError("종료일이 시작일보다 앞입니다.")
    span = (end - start).days
    if span > MAX_CALENDAR_DAYS:
        raise ValueError(f"기간이 너무 깁니다(최대 {MAX_CALENDAR_DAYS}일, 입력 {span}일).")

    natal = build_pillars(birth)

    calendar: list[ds.CandidateDate] = []
    cur = start
    while cur <= end:
        calendar.append(ds.score_date(cur, natal, event_type))
        cur = cur + timedelta(days=1)

    # 길일: score >= 1.0(길/대길), 점수 내림차순·날짜 빠른 순
    best = sorted(
        (c for c in calendar if c.score >= 1.0),
        key=lambda c: (-c.score, c.date),
    )[: max(1, top_n)]
    # 피할 날: score <= -1.0(주의/흉), 점수 오름차순·날짜 빠른 순
    avoid = sorted(
        (c for c in calendar if c.score <= -1.0),
        key=lambda c: (c.score, c.date),
    )[: max(1, top_n)]

    return TimingResult(
        event_type=event_type,
        start=start,
        end=end,
        natal=natal,
        calendar=calendar,
        best=best,
        avoid=avoid,
    )


def summarize_for_llm(candidates: list[ds.CandidateDate]) -> str:
    """LLM 내러티브 입력용 압축 요약 — 'YYYY-MM-DD (간지/라벨/점수): 근거'."""
    lines = []
    for c in candidates:
        gz = f"{c.day_pillar.gan}{c.day_pillar.ji}"
        reasons = "; ".join(c.reasons[:3])
        lines.append(f"{c.date.isoformat()} {gz} [{c.label} {c.score:+.1f}] {reasons}")
    return "\n".join(lines)

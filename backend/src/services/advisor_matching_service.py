"""자문위원 매칭 알고리즘 — Sprint 5-6 베타 핵심.

원칙 (BM v2 + 단위경제 검증 반영):
  1. 가용 시간 절대 — 자문위원이 등록한 weekly availability 슬롯만 매칭
  2. weekly_hours_max 초과 금지 — 자문위원 번아웃 차단
  3. 만족도 가중 — 평균 NPS 높은 자문위원 우선 (사용자 경험)
  4. 라운드로빈 — 같은 만족도면 이번 달 세션 수 최소 자문위원 (균등 분배)
  5. 등급 매칭 — VIP 사용자 → 1급 자문위원 우선 (옵션)

순수 함수 위주 — DB 의존 없이 매칭 로직 테스트 가능.
DB wrapper는 가용 자문위원 조회·세션 생성 시만 활성.

매칭 실패 시: 사용자에게 "다음 가능 시각 안내" 또는 환불 옵션 제공.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta


# ── 데이터 클래스 ────────────────────────────────────────
@dataclass(slots=True)
class TimeSlot:
    """자문위원 가용 슬롯 (UTC)."""

    start: datetime
    end: datetime

    def contains(self, t: datetime) -> bool:
        return self.start <= t < self.end


@dataclass(slots=True)
class AdvisorCandidate:
    """매칭 후보 자문위원의 스냅샷."""

    advisor_id: int
    name: str
    grade: str | None  # "tier1" / "tier2" / None
    is_active: bool
    weekly_hours_max: int

    availability: list[TimeSlot] = field(default_factory=list)

    # 이번 주 누적 시간 (분)
    this_week_minutes: int = 0
    # 이번 달 세션 수 (라운드로빈 기준)
    this_month_session_count: int = 0
    # 최근 평균 만족도 (1~10), 데이터 없으면 None
    avg_satisfaction: float | None = None

    @property
    def available_hours_left_this_week(self) -> float:
        used_hours = self.this_week_minutes / 60
        return max(0.0, self.weekly_hours_max - used_hours)


@dataclass(slots=True)
class MatchRequest:
    """사용자 매칭 요청."""

    user_id: int
    requested_time: datetime
    duration_min: int = 30
    user_tier: str = "premium"  # premium / family / pro
    require_tier1: bool = False  # VIP 요구 시 1급만


@dataclass(slots=True)
class MatchResult:
    """매칭 결과."""

    advisor: AdvisorCandidate | None
    reason: str  # 매칭 사유 (감사·디버그)


# ── 매칭 알고리즘 ────────────────────────────────────────
def filter_available(
    candidates: list[AdvisorCandidate],
    request: MatchRequest,
) -> list[AdvisorCandidate]:
    """매칭 가능한 자문위원만 필터."""
    end_time = request.requested_time + timedelta(minutes=request.duration_min)
    out: list[AdvisorCandidate] = []
    for c in candidates:
        if not c.is_active:
            continue
        if request.require_tier1 and c.grade != "tier1":
            continue
        # 이번 주 가용 시간 안에 들어가는가
        if c.available_hours_left_this_week * 60 < request.duration_min:
            continue
        # 요청 시각이 가용 슬롯 안에 들어가는가
        if not any(
            slot.contains(request.requested_time) and slot.contains(end_time - timedelta(seconds=1))
            for slot in c.availability
        ):
            continue
        out.append(c)
    return out


def rank_candidates(
    candidates: list[AdvisorCandidate],
) -> list[AdvisorCandidate]:
    """매칭 가능 후보를 우선순위로 정렬.

    1순위: 만족도 ≥ 8.0 (높을수록 먼저)
    2순위: 이번 달 세션 수 적은 자문위원 (라운드로빈)
    3순위: 1급 자문위원 우선 (희소 자원)
    4순위: weekly_hours 잔여 많은 자문위원
    """
    def sort_key(c: AdvisorCandidate) -> tuple:
        # avg_satisfaction None 이면 5.0 으로 가정 (중립)
        sat = c.avg_satisfaction if c.avg_satisfaction is not None else 5.0
        return (
            -sat,                              # 만족도 desc
            c.this_month_session_count,        # 세션 수 asc
            0 if c.grade == "tier1" else 1,    # 1급 우선
            -c.available_hours_left_this_week, # 잔여 시간 desc
        )

    return sorted(candidates, key=sort_key)


def match_advisor(
    candidates: list[AdvisorCandidate],
    request: MatchRequest,
) -> MatchResult:
    """매칭 알고리즘 메인.

    Returns:
        MatchResult(advisor=None, reason="...") 매칭 실패 시 사유 명시.
    """
    if not candidates:
        return MatchResult(None, "no_candidates")

    available = filter_available(candidates, request)
    if not available:
        return MatchResult(None, "no_available_in_time_window")

    ranked = rank_candidates(available)
    winner = ranked[0]

    sat_label = (
        f"{winner.avg_satisfaction:.1f}"
        if winner.avg_satisfaction is not None
        else "no_data"
    )
    reason = (
        f"matched: id={winner.advisor_id} grade={winner.grade or '-'} "
        f"sat={sat_label} this_month={winner.this_month_session_count}"
    )
    return MatchResult(winner, reason)


# ── 가용 슬롯 헬퍼 ───────────────────────────────────────
def weekly_availability_to_slots(
    weekday_hours: dict[int, list[tuple[time, time]]],
    week_start: datetime,
) -> list[TimeSlot]:
    """주간 정기 스케줄 → 특정 주(week_start) 의 TimeSlot 목록.

    weekday_hours: {0(월): [(09:00, 12:00), (14:00, 18:00)], 1(화): [...]}
    week_start: UTC 자정의 월요일 datetime
    """
    out: list[TimeSlot] = []
    for weekday_idx, ranges in weekday_hours.items():
        day = week_start + timedelta(days=weekday_idx)
        for start_t, end_t in ranges:
            start = datetime.combine(day.date(), start_t, tzinfo=UTC)
            end = datetime.combine(day.date(), end_t, tzinfo=UTC)
            out.append(TimeSlot(start, end))
    return out


# ── DB Wrapper ───────────────────────────────────────────
def _db_enabled() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


async def fetch_available_candidates(
    requested_time: datetime,
    require_tier1: bool = False,
) -> list[AdvisorCandidate]:
    """DB에서 활성 자문위원 + 통계 조회 후 AdvisorCandidate 목록.

    DB 미설정 시 빈 리스트.
    실제 가용 슬롯 정보는 advisor_availability 테이블(미래) 또는
    자문위원이 등록한 캘린더 동기화에서.
    """
    if not _db_enabled():
        return []

    from sqlalchemy import and_, func, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import Advisor, AdvisorSession

    session: AsyncSession
    async with _session_factory()() as session:
        # 활성 자문위원
        stmt = select(Advisor).where(Advisor.is_active)
        if require_tier1:
            stmt = stmt.where(Advisor.grade == "tier1")
        advisors = (await session.execute(stmt)).scalars().all()

        # 이번 달 세션 카운트
        month_start = datetime(
            requested_time.year, requested_time.month, 1, tzinfo=UTC,
        )
        next_month = (
            month_start.replace(year=month_start.year + 1, month=1)
            if month_start.month == 12
            else month_start.replace(month=month_start.month + 1)
        )
        sess_count_stmt = (
            select(AdvisorSession.advisor_id, func.count(AdvisorSession.id))
            .where(and_(
                AdvisorSession.scheduled_at >= month_start,
                AdvisorSession.scheduled_at < next_month,
                AdvisorSession.status.in_(["scheduled", "completed"]),
            ))
            .group_by(AdvisorSession.advisor_id)
        )
        rows = await session.execute(sess_count_stmt)
        month_count = {advisor_id: cnt for advisor_id, cnt in rows.all()}

        # 평균 만족도 (이번 분기)
        quarter_start = month_start - timedelta(days=90)
        sat_stmt = (
            select(
                AdvisorSession.advisor_id,
                func.avg(AdvisorSession.satisfaction_score),
            )
            .where(and_(
                AdvisorSession.satisfaction_score.is_not(None),
                AdvisorSession.scheduled_at >= quarter_start,
            ))
            .group_by(AdvisorSession.advisor_id)
        )
        rows = await session.execute(sat_stmt)
        avg_sat = {advisor_id: float(avg) for advisor_id, avg in rows.all() if avg is not None}

        # 후보 빌드 (availability 는 별도 시스템에서 동기화 — 현재는 빈 리스트)
        return [
            AdvisorCandidate(
                advisor_id=a.id,
                name=a.name,
                grade=a.grade,
                is_active=a.is_active,
                weekly_hours_max=a.weekly_hours_max,
                availability=[],  # TODO Sprint 7-8: advisor_availability 테이블
                this_week_minutes=0,
                this_month_session_count=month_count.get(a.id, 0),
                avg_satisfaction=avg_sat.get(a.id),
            )
            for a in advisors
        ]


async def create_session(
    user_id: int,
    advisor_id: int,
    scheduled_at: datetime,
    duration_min: int = 30,
    subscription_id: int | None = None,
) -> int | None:
    """매칭 성공 후 advisor_session 레코드 생성.

    Returns: 생성된 session id (DB 비활성 시 None)
    """
    if not _db_enabled():
        return None

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import AdvisorSession

    session: AsyncSession
    async with _session_factory()() as session:
        row = AdvisorSession(
            user_id=user_id,
            advisor_id=advisor_id,
            subscription_id=subscription_id,
            scheduled_at=scheduled_at,
            duration_min=duration_min,
            status="scheduled",
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row.id

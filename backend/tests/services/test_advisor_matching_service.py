"""services.advisor_matching_service 단위 테스트.

매칭 알고리즘 — 가용성·만족도·라운드로빈·등급 우선순위 검증.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest

from src.services.advisor_matching_service import (
    AdvisorCandidate,
    MatchRequest,
    TimeSlot,
    create_session,
    fetch_available_candidates,
    filter_available,
    match_advisor,
    rank_candidates,
    weekly_availability_to_slots,
)


# ── 헬퍼: 테스트용 자문위원 빌더 ────────────────────────
def make_advisor(
    aid: int,
    grade: str | None = "tier2",
    active: bool = True,
    weekly_max: int = 40,
    weekly_used_min: int = 0,
    this_month: int = 0,
    sat: float | None = 7.0,
    available: list[TimeSlot] | None = None,
) -> AdvisorCandidate:
    return AdvisorCandidate(
        advisor_id=aid,
        name=f"Advisor-{aid}",
        grade=grade,
        is_active=active,
        weekly_hours_max=weekly_max,
        availability=available or [],
        this_week_minutes=weekly_used_min,
        this_month_session_count=this_month,
        avg_satisfaction=sat,
    )


def make_request(
    user_id: int = 100,
    when: datetime | None = None,
    require_tier1: bool = False,
) -> MatchRequest:
    return MatchRequest(
        user_id=user_id,
        requested_time=when or datetime(2026, 6, 15, 14, 0, tzinfo=UTC),
        duration_min=30,
        require_tier1=require_tier1,
    )


def slot_around(when: datetime, hours: int = 2) -> TimeSlot:
    """when 전후로 N시간 가용 슬롯."""
    return TimeSlot(
        start=when - timedelta(hours=hours),
        end=when + timedelta(hours=hours),
    )


# ── filter_available — 가용성 필터 ───────────────────────
def test_filter_inactive_excluded() -> None:
    when = datetime(2026, 6, 15, 14, 0, tzinfo=UTC)
    req = make_request(when=when)
    advisors = [
        make_advisor(1, active=True, available=[slot_around(when)]),
        make_advisor(2, active=False, available=[slot_around(when)]),
    ]
    out = filter_available(advisors, req)
    assert len(out) == 1
    assert out[0].advisor_id == 1


def test_filter_no_availability_excluded() -> None:
    """요청 시각에 가용 슬롯 없으면 제외."""
    when = datetime(2026, 6, 15, 14, 0, tzinfo=UTC)
    req = make_request(when=when)
    far_slot = TimeSlot(
        start=when + timedelta(days=1),
        end=when + timedelta(days=1, hours=1),
    )
    advisors = [
        make_advisor(1, available=[slot_around(when)]),
        make_advisor(2, available=[far_slot]),
    ]
    out = filter_available(advisors, req)
    assert len(out) == 1
    assert out[0].advisor_id == 1


def test_filter_weekly_hours_exceeded() -> None:
    """weekly_hours_max 초과한 자문위원 제외."""
    when = datetime(2026, 6, 15, 14, 0, tzinfo=UTC)
    req = make_request(when=when)
    # 1번: 10시간 max에 10시간 사용 = 한도 도달
    advisors = [
        make_advisor(1, weekly_max=10, weekly_used_min=600, available=[slot_around(when)]),
        make_advisor(2, weekly_max=40, weekly_used_min=300, available=[slot_around(when)]),
    ]
    out = filter_available(advisors, req)
    assert len(out) == 1
    assert out[0].advisor_id == 2


def test_filter_tier1_only() -> None:
    """require_tier1 시 1급만."""
    when = datetime(2026, 6, 15, 14, 0, tzinfo=UTC)
    req = make_request(when=when, require_tier1=True)
    advisors = [
        make_advisor(1, grade="tier1", available=[slot_around(when)]),
        make_advisor(2, grade="tier2", available=[slot_around(when)]),
    ]
    out = filter_available(advisors, req)
    assert len(out) == 1
    assert out[0].advisor_id == 1


# ── rank_candidates — 우선순위 ──────────────────────────
def test_rank_by_satisfaction() -> None:
    """만족도 높은 자문위원 우선."""
    advisors = [
        make_advisor(1, sat=7.0),
        make_advisor(2, sat=9.5),
        make_advisor(3, sat=8.0),
    ]
    ranked = rank_candidates(advisors)
    assert [c.advisor_id for c in ranked] == [2, 3, 1]


def test_rank_round_robin_same_satisfaction() -> None:
    """같은 만족도면 이번 달 세션 수 적은 자문위원 우선 (라운드로빈)."""
    advisors = [
        make_advisor(1, sat=8.0, this_month=10),
        make_advisor(2, sat=8.0, this_month=2),
        make_advisor(3, sat=8.0, this_month=5),
    ]
    ranked = rank_candidates(advisors)
    assert [c.advisor_id for c in ranked] == [2, 3, 1]


def test_rank_tier1_priority() -> None:
    """같은 만족도·세션 수면 1급 우선."""
    advisors = [
        make_advisor(1, sat=8.0, this_month=5, grade="tier2"),
        make_advisor(2, sat=8.0, this_month=5, grade="tier1"),
    ]
    ranked = rank_candidates(advisors)
    assert ranked[0].advisor_id == 2


def test_rank_no_satisfaction_data_neutral() -> None:
    """만족도 None 인 자문위원은 중립 5.0 으로 가정."""
    advisors = [
        make_advisor(1, sat=6.0),
        make_advisor(2, sat=None),
        make_advisor(3, sat=4.0),
    ]
    ranked = rank_candidates(advisors)
    # 6.0 > 5.0(None) > 4.0
    assert [c.advisor_id for c in ranked] == [1, 2, 3]


# ── match_advisor — 통합 ─────────────────────────────────
def test_match_returns_best_candidate() -> None:
    when = datetime(2026, 6, 15, 14, 0, tzinfo=UTC)
    req = make_request(when=when)
    advisors = [
        make_advisor(1, sat=7.5, this_month=10, available=[slot_around(when)]),
        make_advisor(2, sat=9.0, this_month=3, available=[slot_around(when)]),  # 최적
        make_advisor(3, sat=9.0, this_month=8, available=[slot_around(when)]),
    ]
    result = match_advisor(advisors, req)
    assert result.advisor is not None
    assert result.advisor.advisor_id == 2
    assert "matched" in result.reason


def test_match_no_candidates() -> None:
    result = match_advisor([], make_request())
    assert result.advisor is None
    assert result.reason == "no_candidates"


def test_match_no_available_in_window() -> None:
    """가용 자문위원 없으면 명확한 사유."""
    when = datetime(2026, 6, 15, 14, 0, tzinfo=UTC)
    req = make_request(when=when)
    # 모두 다른 시간대 가용
    far_slot = TimeSlot(
        start=when + timedelta(days=10),
        end=when + timedelta(days=10, hours=2),
    )
    advisors = [make_advisor(1, available=[far_slot])]
    result = match_advisor(advisors, req)
    assert result.advisor is None
    assert result.reason == "no_available_in_time_window"


# ── weekly_availability_to_slots ─────────────────────────
def test_weekly_to_slots_simple() -> None:
    week_start = datetime(2026, 6, 15, 0, 0, tzinfo=UTC)  # 월요일
    weekly = {
        0: [(time(9, 0), time(12, 0))],   # 월 9-12
        2: [(time(14, 0), time(18, 0))],  # 수 14-18
    }
    slots = weekly_availability_to_slots(weekly, week_start)
    assert len(slots) == 2
    # 월요일 9-12
    assert slots[0].start == datetime(2026, 6, 15, 9, 0, tzinfo=UTC)
    assert slots[0].end == datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    # 수요일 14-18
    assert slots[1].start == datetime(2026, 6, 17, 14, 0, tzinfo=UTC)
    assert slots[1].end == datetime(2026, 6, 17, 18, 0, tzinfo=UTC)


# ── TimeSlot.contains ────────────────────────────────────
def test_timeslot_contains() -> None:
    slot = TimeSlot(
        start=datetime(2026, 6, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 6, 15, 16, 0, tzinfo=UTC),
    )
    assert slot.contains(datetime(2026, 6, 15, 14, 0, tzinfo=UTC))
    assert slot.contains(datetime(2026, 6, 15, 15, 30, tzinfo=UTC))
    assert not slot.contains(datetime(2026, 6, 15, 16, 0, tzinfo=UTC))  # end 포함 X
    assert not slot.contains(datetime(2026, 6, 15, 13, 59, tzinfo=UTC))


# ── DB Wrapper — DATABASE_URL 없음 시 안전 ───────────────
@pytest.mark.asyncio
async def test_fetch_returns_empty_without_db() -> None:
    import os
    os.environ.pop("DATABASE_URL", None)
    rv = await fetch_available_candidates(datetime.now(UTC))
    assert rv == []


@pytest.mark.asyncio
async def test_create_session_returns_none_without_db() -> None:
    import os
    os.environ.pop("DATABASE_URL", None)
    rv = await create_session(
        user_id=1, advisor_id=1, scheduled_at=datetime.now(UTC),
    )
    assert rv is None


# ── 실 시나리오 ──────────────────────────────────────────
def test_realistic_scenario_5_advisors() -> None:
    """5명 자문위원 중 최적 매칭 — 만족도 + 라운드로빈."""
    when = datetime(2026, 6, 15, 14, 0, tzinfo=UTC)
    slot = slot_around(when)
    req = make_request(when=when)
    # 3번이 최적: 1급 + 만족도 9.5 + 이번달 3건 (= 1번보다 적음)
    advisors = [
        make_advisor(1, grade="tier1", sat=9.5, this_month=15, available=[slot]),
        make_advisor(2, grade="tier2", sat=8.0, this_month=2, available=[slot]),
        make_advisor(3, grade="tier1", sat=9.5, this_month=3, available=[slot]),
        make_advisor(4, grade="tier2", sat=7.0, this_month=1, available=[slot]),
        make_advisor(5, grade="tier1", sat=6.5, this_month=20, available=[slot]),
    ]
    result = match_advisor(advisors, req)
    assert result.advisor is not None
    # 3번 자문위원: 만족도 9.5 + 이번달 3건 (= 1번보다 적음)
    assert result.advisor.advisor_id == 3

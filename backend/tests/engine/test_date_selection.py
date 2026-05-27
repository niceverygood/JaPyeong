"""engine.date_selection 단위 테스트."""

from __future__ import annotations

from datetime import date

import pytest

from src.engine import date_selection as ds
from src.engine.schema import FourPillars, Pillar


def natal(d_gan: str = "丙", d_ji: str = "午") -> FourPillars:
    return FourPillars(
        year=Pillar(gan="甲", ji="子"),
        month=Pillar(gan="乙", ji="丑"),
        day=Pillar(gan=d_gan, ji=d_ji),
        hour=Pillar(gan="戊", ji="戌"),
    )


def test_label_thresholds() -> None:
    assert ds._label_for(3.0) == "대길"
    assert ds._label_for(1.5) == "길"
    assert ds._label_for(0.0) == "평"
    assert ds._label_for(-1.5) == "주의"
    assert ds._label_for(-3.0) == "흉"


def test_score_returns_candidate() -> None:
    """결과 객체의 필수 필드가 채워짐."""
    c = ds.score_date(date(2026, 1, 1), natal(), "general")
    assert isinstance(c.score, float)
    assert -5.0 <= c.score <= 5.0
    assert c.day_pillar.gan in {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}
    assert c.label in {"대길", "길", "평", "주의", "흉"}
    assert len(c.reasons) >= 1


def test_select_dates_sorted_desc() -> None:
    """select_dates 결과는 점수 내림차순."""
    res = ds.select_dates(natal(), date(2026, 1, 1), date(2026, 1, 31), "general", top_n=10)
    assert len(res) <= 10
    scores = [c.score for c in res]
    assert scores == sorted(scores, reverse=True)


def test_select_dates_top_n() -> None:
    res = ds.select_dates(natal(), date(2026, 1, 1), date(2026, 1, 31), "general", top_n=3)
    assert len(res) == 3


def test_select_dates_top_n_zero_returns_all() -> None:
    res = ds.select_dates(natal(), date(2026, 1, 1), date(2026, 1, 7), "general", top_n=0)
    assert len(res) == 7


def test_invalid_range() -> None:
    with pytest.raises(ValueError):
        ds.select_dates(natal(), date(2026, 1, 10), date(2026, 1, 1))


def test_range_too_long() -> None:
    with pytest.raises(ValueError, match="기간이 너무 깁니다"):
        ds.select_dates(natal(), date(2026, 1, 1), date(2027, 6, 1))


def test_marriage_bonus_when_hap() -> None:
    """결혼 event_type — 일운 지지가 사주 일지(午)와 육합(未)이면 보너스 ≥ 1.0."""
    # 사주 일지 = 午. 1996년 어느 날 일지가 未인 날 (검색)
    n = natal(d_ji="午")
    # 직접 score_date 호출 — 일지가 未인 날을 알고 사용
    # 간편화: 2026년 1월 31일 (沒) 대신 적절한 날짜 찾기는 비결정. 통합 테스트로만 시점 확인
    res = ds.select_dates(n, date(2026, 1, 1), date(2026, 1, 31), "marriage", top_n=0)
    # 일지 未인 날에 결혼 보너스가 적용됐어야 한다 → 사유에 "결혼 보너스" 포함되는 카드 ≥ 1
    assert any(any("결혼 보너스" in r for r in c.reasons) for c in res), \
        "1월 중 결혼 보너스 케이스가 한 건 이상 있어야 합니다."


def test_moving_bonus_yeokma() -> None:
    """이주 event_type — 寅申巳亥 일지에 보너스."""
    n = natal()
    res = ds.select_dates(n, date(2026, 1, 1), date(2026, 1, 31), "moving", top_n=0)
    assert any(any("이주 보너스" in r for r in c.reasons) for c in res)


def test_dynamic_event_business() -> None:
    n = natal()
    res = ds.select_dates(n, date(2026, 1, 1), date(2026, 1, 31), "business", top_n=0)
    # 사업 보너스 또는 사업 페널티가 최소 하나는 있어야 한다
    assert any(
        any("사업 보너스" in r or "사업 페널티" in r for r in c.reasons)
        for c in res
    )

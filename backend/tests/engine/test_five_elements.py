"""오행 분포 모듈 검증 테스트 (TDD — 구현 전 작성).

오행 가중치 분포는 가중치 정의에 따라 달라지므로 ElementWeights를 외부 주입.
default는 보수값(자평진전 계열), 정책 마킹 아님.
"""

import pytest

from src.engine import five_elements as fe
from src.engine.constants import Ohaeng
from src.engine.schema import FourPillars, Pillar


def _p(gan: str, ji: str) -> Pillar:
    return Pillar(gan=gan, ji=ji)


# 균형 근사 사주: 木2 火2 土2 金1 水1 (include_hidden=False, 8자)
BALANCED = FourPillars(
    year=_p("甲", "子"), month=_p("丙", "寅"), day=_p("戊", "辰"), hour=_p("庚", "午")
)
# 단일 오행(水): 壬子 ×4 — 천간·지지·지장간 모두 水
PURE_SU = FourPillars(
    year=_p("壬", "子"), month=_p("壬", "子"), day=_p("壬", "子"), hour=_p("壬", "子")
)
# 편중 사주: 水6 木2
SKEWED = FourPillars(
    year=_p("壬", "子"), month=_p("壬", "子"), day=_p("壬", "子"), hour=_p("甲", "寅")
)


def test_single_element_chart_all_in_one():
    dist = fe.calculate_distribution(PURE_SU, include_hidden=True)
    assert dist.mok == 0 and dist.hwa == 0 and dist.to == 0 and dist.geum == 0
    assert dist.su == dist.total > 0
    assert fe.get_dominant_element(dist) == Ohaeng.SU


def test_balanced_chart_high_score():
    dist = fe.calculate_distribution(BALANCED, include_hidden=False)
    # 木2 火2 土2 金1 水1
    assert (dist.mok, dist.hwa, dist.to, dist.geum, dist.su) == (2, 2, 2, 1, 1)
    assert dist.total == 8
    assert fe.get_balance_score(dist) >= 0.85


def test_skewed_chart_low_score():
    dist = fe.calculate_distribution(SKEWED, include_hidden=False)
    assert fe.get_balance_score(dist) < 0.5
    assert fe.get_dominant_element(dist) == Ohaeng.SU


def test_include_hidden_changes_result():
    no_hidden = fe.calculate_distribution(BALANCED, include_hidden=False)
    with_hidden = fe.calculate_distribution(BALANCED, include_hidden=True)
    # 中氣·餘氣가 추가되므로 total 증가
    assert with_hidden.total > no_hidden.total


def test_element_weights_residual_zero():
    default = fe.calculate_distribution(PURE_SU, include_hidden=True)
    w = fe.ElementWeights(branch_residual_weight=0.0)
    no_res = fe.calculate_distribution(PURE_SU, include_hidden=True, weights=w)
    # 子의 餘氣(壬)이 빠지므로 total 감소 (둘 다 水지만 합계 달라짐)
    assert no_res.total < default.total
    assert no_res.su == no_res.total  # 여전히 전부 水


@pytest.mark.parametrize(
    "pillars,dominant,weakest",
    [
        (PURE_SU, Ohaeng.SU, Ohaeng.MOK),  # 水만 → 나머지 동률, 정렬상 木
        (SKEWED, Ohaeng.SU, Ohaeng.HWA),  # 水6 木2, 火土금 0 → 정렬상 火
    ],
)
def test_dominant_and_weakest(pillars, dominant, weakest):
    dist = fe.calculate_distribution(pillars, include_hidden=False)
    assert fe.get_dominant_element(dist) == dominant
    assert fe.get_weakest_element(dist) == weakest


def test_dominant_weakest_on_balanced():
    dist = fe.calculate_distribution(BALANCED, include_hidden=False)
    assert fe.get_dominant_element(dist) in (Ohaeng.MOK, Ohaeng.HWA, Ohaeng.TO)
    assert fe.get_weakest_element(dist) in (Ohaeng.GEUM, Ohaeng.SU)


def test_breakdown_tracks_all_8_chars():
    dist = fe.calculate_distribution(BALANCED, include_hidden=False)
    sources = {c.source for contribs in dist.breakdown.values() for c in contribs}
    expected = {
        "year_gan", "month_gan", "day_gan", "hour_gan",
        "year_ji_primary", "month_ji_primary", "day_ji_primary", "hour_ji_primary",
    }
    assert sources == expected
    # 가중치 합이 분포 total과 일치 (추적 무결성)
    total_weight = sum(c.weight for cs in dist.breakdown.values() for c in cs)
    assert total_weight == pytest.approx(dist.total)


def test_hour_none_excluded():
    pillars = FourPillars(year=_p("甲", "子"), month=_p("丙", "寅"), day=_p("戊", "辰"))
    dist = fe.calculate_distribution(pillars, include_hidden=False)
    sources = {c.source for cs in dist.breakdown.values() for c in cs}
    assert not any("hour" in s for s in sources)
    assert dist.total == 6  # 3 천간 + 3 지지 본기

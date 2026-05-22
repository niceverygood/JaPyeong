"""24절기 모듈 검증 테스트 (TDD — 구현 전 작성).

월주 경계는 12절(節, 홀수 jieqi)을 따른다(WoljuBoundaryPolicy.JEOL).
세수는 입춘 기준(SesuPolicy.IPCHUN).
절입 시각은 sxtwl에서 산출 후 KST(naive)로 환산 — 검증된 캘리브레이션 사용.

순수 결정론적: 같은 입력 → 항상 같은 출력.
"""

from dataclasses import replace
from datetime import datetime

import pytest

from src.engine import jeolgi
from src.engine.policy import SesuPolicy, WoljuBoundaryPolicy, get_default_policy


# ── 절입 시각 환산 (알려진 값 대조) ──────────────────────────
def test_ipchun_2024_kst_instant():
    boundaries = jeolgi.jeol_boundaries(2024)
    ipchun = boundaries[0]  # 첫 절 = 입춘
    assert ipchun.month_branch == "寅"
    # 立春 2024 = 2024-02-04 17:26:53 KST (검증된 캘리브레이션)
    assert ipchun.instant.replace(microsecond=0) == datetime(2024, 2, 4, 17, 26, 53)


def test_jeol_boundaries_12_in_order():
    bs = jeolgi.jeol_boundaries(2024)
    assert len(bs) == 12
    branches = [b.month_branch for b in bs]
    assert branches == ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
    assert all(b.is_jeol for b in bs)
    # 시간 순 증가
    assert all(bs[i].instant < bs[i + 1].instant for i in range(11))


# ── 월지 판정 (구간 내부, 분 정밀도 불필요) ───────────────────
@pytest.mark.parametrize(
    "dt,branch",
    [
        (datetime(2024, 3, 15, 12, 0), "卯"),  # 경칩~청명
        (datetime(2024, 7, 20, 9, 0), "未"),  # 소서~입추
        (datetime(2024, 12, 25, 0, 0), "子"),  # 대설 이후
        (datetime(2024, 1, 2, 0, 0), "子"),  # 전년 대설~소한 전
        (datetime(2024, 1, 10, 0, 0), "丑"),  # 소한 이후
        (datetime(2024, 5, 15, 0, 0), "巳"),  # 입하~망종
    ],
)
def test_month_branch_for(dt, branch):
    assert jeolgi.month_branch_for(dt) == branch


def test_month_branch_boundary_exact():
    ipchun = jeolgi.jeol_boundaries(2024)[0].instant
    # 입춘 직전 = 丑(전월), 직후 = 寅
    from datetime import timedelta

    assert jeolgi.month_branch_for(ipchun - timedelta(seconds=1)) == "丑"
    assert jeolgi.month_branch_for(ipchun + timedelta(seconds=1)) == "寅"


# ── 세수(입춘 기준 명리 연도) ─────────────────────────────────
def test_solar_year_ipchun_boundary():
    assert jeolgi.solar_year(datetime(2024, 1, 20)) == 2023
    assert jeolgi.solar_year(datetime(2024, 2, 10)) == 2024
    ipchun = jeolgi.jeol_boundaries(2024)[0].instant
    from datetime import timedelta

    assert jeolgi.solar_year(ipchun - timedelta(seconds=1)) == 2023
    assert jeolgi.solar_year(ipchun + timedelta(seconds=1)) == 2024


# ── 정책 분기 (미지원 옵션은 명시적 차단) ─────────────────────
def test_junggi_policy_not_implemented():
    pol = replace(get_default_policy(), wolju_boundary=WoljuBoundaryPolicy.JUNGGI)
    with pytest.raises(NotImplementedError):
        jeolgi.month_branch_for(datetime(2024, 3, 15), policy=pol)


def test_dongji_sesu_not_implemented():
    pol = replace(get_default_policy(), sesu=SesuPolicy.DONGJI)
    with pytest.raises(NotImplementedError):
        jeolgi.solar_year(datetime(2024, 3, 15), policy=pol)


# ── 결정론성 ──────────────────────────────────────────────────
def test_deterministic():
    dt = datetime(1985, 6, 23, 14, 30)
    assert jeolgi.month_branch_for(dt) == jeolgi.month_branch_for(dt)
    assert jeolgi.solar_year(dt) == jeolgi.solar_year(dt)

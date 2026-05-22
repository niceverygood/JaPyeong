"""대운(大運) 모듈 검증 테스트 (TDD — 구현 전 작성).

방향: 양남음녀 순행(양년 남자/음년 여자 → 순행), 그 외 역행.
대운수: 출생→절입 일수 ÷ 3 (3일=1년), DaewoonCalc.DAYS_DIV3.
대운 간지: 月柱를 기준으로 순행(+) / 역행(-) 진행.

검증 기준값(probe 확정): 1985-06-23 14:30 서울
  남(乙년 음간) → 역행, 대운수 6, 첫 대운 辛巳→庚辰
  여 → 순행, 대운수 5, 첫 대운 癸未→甲申
"""

import pytest

from src.engine import daewoon as dw
from src.engine.ganji import is_valid_ganji
from src.engine.schema import BirthInfo


def _birth(gender="M", **kw) -> BirthInfo:
    base = dict(
        gender=gender, calendar="solar", year=1985, month=6, day=23,
        hour=14, minute=30, longitude=126.9784, latitude=37.5665,
    )
    base.update(kw)
    return BirthInfo(**base)


# ── 방향 (양남음녀 순행) ──────────────────────────────────────
@pytest.mark.parametrize(
    "gan,gender,expected",
    [
        ("甲", "M", "forward"),   # 양년 남
        ("甲", "F", "backward"),  # 양년 여
        ("乙", "M", "backward"),  # 음년 남
        ("乙", "F", "forward"),   # 음년 여
        ("庚", "M", "forward"),   # 양년 남
        ("癸", "F", "forward"),   # 음년 여
        ("壬", "M", "forward"),
        ("辛", "M", "backward"),
    ],
)
def test_direction(gan, gender, expected):
    assert dw.daewoon_direction(gan, gender) == expected


# ── 대운수 (절입 일수 ÷ 3) ────────────────────────────────────
def test_start_age_backward_male():
    periods = dw.build_daewoon(_birth("M"))
    assert dw.daewoon_direction("乙", "M") == "backward"
    assert periods[0].start_age == 6


def test_start_age_forward_female():
    periods = dw.build_daewoon(_birth("F"))
    assert periods[0].start_age == 5


# ── 대운 간지 진행 (月柱 壬午 기준) ───────────────────────────
def test_sequence_backward_male():
    periods = dw.build_daewoon(_birth("M"))
    assert [(p.gan, p.ji) for p in periods[:2]] == [("辛", "巳"), ("庚", "辰")]
    assert [p.start_age for p in periods[:3]] == [6, 16, 26]
    assert [p.sequence for p in periods[:3]] == [1, 2, 3]


def test_sequence_forward_female():
    periods = dw.build_daewoon(_birth("F"))
    assert [(p.gan, p.ji) for p in periods[:2]] == [("癸", "未"), ("甲", "申")]
    assert [p.start_age for p in periods[:2]] == [5, 15]


# ── count / 유효성 ────────────────────────────────────────────
def test_count_default_and_param():
    assert len(dw.build_daewoon(_birth())) == 9
    assert len(dw.build_daewoon(_birth(), count=3)) == 3


def test_all_periods_valid_ganji():
    for p in dw.build_daewoon(_birth()):
        assert is_valid_ganji(p.gan, p.ji), f"{p.gan}{p.ji} 무효"


def test_start_age_function_matches():
    b = _birth("M")
    assert dw.daewoon_start_age(b) == dw.build_daewoon(b)[0].start_age


def test_deterministic():
    b = _birth("M")
    assert dw.build_daewoon(b) == dw.build_daewoon(b)

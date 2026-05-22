"""지장간(地藏干) 모듈 검증 테스트 (TDD — 구현 전 작성).

지장간 배합은 명리 유파 공통(월률분야 통설). 정책 의존 없음 → 결정론적.
일수 배분은 통용 30일 기준표(명리요강 등 다수 교재 공통)를 채택.
"""

import pytest

from src.engine import jijanggan as jjg
from src.engine.constants import JI_JI

# 통용 월률분야 지장간표: 지지 → [(천간, 단계, 일수), ...] (餘氣→中氣→正氣 순)
EXPECTED = {
    "子": [("壬", "餘氣", 10), ("癸", "正氣", 20)],
    "丑": [("癸", "餘氣", 9), ("辛", "中氣", 3), ("己", "正氣", 18)],
    "寅": [("戊", "餘氣", 7), ("丙", "中氣", 7), ("甲", "正氣", 16)],
    "卯": [("甲", "餘氣", 10), ("乙", "正氣", 20)],
    "辰": [("乙", "餘氣", 9), ("癸", "中氣", 3), ("戊", "正氣", 18)],
    "巳": [("戊", "餘氣", 7), ("庚", "中氣", 7), ("丙", "正氣", 16)],
    "午": [("丙", "餘氣", 10), ("己", "中氣", 9), ("丁", "正氣", 11)],
    "未": [("丁", "餘氣", 9), ("乙", "中氣", 3), ("己", "正氣", 18)],
    "申": [("戊", "餘氣", 7), ("壬", "中氣", 7), ("庚", "正氣", 16)],
    "酉": [("庚", "餘氣", 10), ("辛", "正氣", 20)],
    "戌": [("辛", "餘氣", 9), ("丁", "中氣", 3), ("戊", "正氣", 18)],
    "亥": [("戊", "餘氣", 7), ("甲", "中氣", 7), ("壬", "正氣", 16)],
}

# 中氣가 없는 지지 3개
NO_JUNGGI = ("子", "卯", "酉")


@pytest.mark.parametrize("ji", JI_JI)
def test_jijanggan_exact(ji):
    """12지지 전체 지장간(천간·단계·일수) 정확성."""
    result = jjg.get_jijanggan(ji)
    got = [(h.gan, h.stage.value, h.days) for h in result]
    assert got == EXPECTED[ji], f"{ji} 지장간 불일치"


@pytest.mark.parametrize("ji", NO_JUNGGI)
def test_no_junggi_branches_have_two_stems(ji):
    """子·卯·酉는 中氣 없이 餘氣·正氣 2원소만."""
    result = jjg.get_jijanggan(ji)
    assert len(result) == 2
    assert all(h.stage != jjg.StageType.JUNGGI for h in result)


@pytest.mark.parametrize("ji", JI_JI)
def test_days_sum_30(ji):
    """지장간 일수 합은 30 (±1 허용)."""
    total = sum(h.days for h in jjg.get_jijanggan(ji))
    assert abs(total - 30) <= 1, f"{ji} 일수 합 {total}"


@pytest.mark.parametrize("ji", JI_JI)
def test_primary_stem_is_jeonggi(ji):
    """get_primary_stem은 正氣 천간만 반환."""
    primary = jjg.get_primary_stem(ji)
    jeonggi = next(h.gan for h in jjg.get_jijanggan(ji) if h.stage == jjg.StageType.JEONGGI)
    assert primary == jeonggi
    # EXPECTED 표의 마지막(正氣)과도 일치
    assert primary == EXPECTED[ji][-1][0]


def test_invalid_ji_raises():
    with pytest.raises(ValueError):
        jjg.get_jijanggan("甲")  # 천간을 지지로
    with pytest.raises(ValueError):
        jjg.get_primary_stem("X")


def test_hidden_stem_immutable():
    from dataclasses import FrozenInstanceError

    h = jjg.get_jijanggan("寅")[0]
    with pytest.raises(FrozenInstanceError):
        h.days = 99  # type: ignore[misc]

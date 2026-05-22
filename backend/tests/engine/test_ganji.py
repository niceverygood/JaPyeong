"""ganji 모듈 검증 테스트 (TDD — 구현 전 작성).

60갑자는 명리 공통 기초이므로 결과가 결정론적·불변이다.
간지 변환은 8자 추출의 토대 → 100% 일치 요구.
"""

import pytest

from src.engine import ganji
from src.engine.constants import Eumyang, Ohaeng


# ── index ↔ ganji 왕복 ────────────────────────────────────────
@pytest.mark.parametrize(
    "idx,gan,ji",
    [
        (0, "甲", "子"),
        (1, "乙", "丑"),
        (2, "丙", "寅"),
        (10, "甲", "戌"),  # 천간 한 바퀴(10) 후
        (12, "丙", "子"),  # 지지 한 바퀴(12) 후
        (59, "癸", "亥"),
    ],
)
def test_index_to_ganji(idx, gan, ji):
    assert ganji.ganji_by_index(idx) == (gan, ji)
    assert ganji.ganji_index(gan, ji) == idx


def test_index_wraps_mod_60():
    assert ganji.ganji_by_index(60) == ("甲", "子")
    assert ganji.ganji_by_index(61) == ("乙", "丑")
    assert ganji.ganji_by_index(-1) == ("癸", "亥")


# ── 유효하지 않은 간지 조합 ───────────────────────────────────
@pytest.mark.parametrize("gan,ji", [("甲", "丑"), ("乙", "子"), ("丙", "卯")])
def test_invalid_ganji_pair_raises(gan, ji):
    # 천간(양/음)과 지지(양/음) 음양이 어긋나면 60갑자에 존재하지 않음.
    with pytest.raises(ValueError):
        ganji.ganji_index(gan, ji)


def test_is_valid_ganji():
    assert ganji.is_valid_ganji("甲", "子") is True
    assert ganji.is_valid_ganji("甲", "丑") is False


# ── 다음/이전 간지 (60 순환) ──────────────────────────────────
def test_next_ganji_wraps():
    assert ganji.next_ganji("癸", "亥") == ("甲", "子")


def test_next_ganji_step():
    assert ganji.next_ganji("甲", "子", step=2) == ("丙", "寅")
    assert ganji.next_ganji("甲", "子", step=-1) == ("癸", "亥")


# ── 인덱스 조회 ───────────────────────────────────────────────
def test_gan_ji_index():
    assert ganji.gan_index("甲") == 0
    assert ganji.gan_index("癸") == 9
    assert ganji.ji_index("子") == 0
    assert ganji.ji_index("亥") == 11


def test_invalid_gan_ji_index_raises():
    with pytest.raises(ValueError):
        ganji.gan_index("子")  # 지지를 천간으로
    with pytest.raises(ValueError):
        ganji.ji_index("甲")  # 천간을 지지로


# ── 오행 / 음양 ───────────────────────────────────────────────
def test_ohaeng():
    assert ganji.gan_ohaeng("甲") == Ohaeng.MOK
    assert ganji.gan_ohaeng("壬") == Ohaeng.SU
    assert ganji.ji_ohaeng("午") == Ohaeng.HWA
    assert ganji.ji_ohaeng("子") == Ohaeng.SU


def test_eumyang():
    assert ganji.gan_eumyang("甲") == Eumyang.YANG
    assert ganji.gan_eumyang("乙") == Eumyang.EUM
    assert ganji.ji_eumyang("子") == Eumyang.YANG
    assert ganji.ji_eumyang("丑") == Eumyang.EUM

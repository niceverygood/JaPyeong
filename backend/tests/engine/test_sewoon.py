"""세운·월운·일운 모듈 검증 테스트 (TDD — 구현 전 작성).

세운: 명리 연도(입춘 세수) 간지 — 1984 甲子 anchor.
월운: 해당 시각의 절기 월지 + 세운 년간 五虎遁.
일운: 해당 양력일의 일주(sxtwl, 검증 완료).

기준값은 sxtwl getYearGZ/getMonthGZ/getDayGZ와 교차검증됨.
"""

from datetime import date, datetime

import pytest

from src.engine import sewoon as sw
from src.engine.ganji import is_valid_ganji


# ── 세운 ──────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "year,gan,ji",
    [(1984, "甲", "子"), (1985, "乙", "丑"), (2024, "甲", "辰"), (2000, "庚", "辰")],
)
def test_se_un(year, gan, ji):
    p = sw.se_un(year)
    assert (p.gan, p.ji) == (gan, ji)


def test_se_un_range():
    rng = sw.se_un_range(1984, count=3)
    assert [(y, p.gan + p.ji) for y, p in rng] == [(1984, "甲子"), (1985, "乙丑"), (1986, "丙寅")]


# ── 월운 ──────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "dt,ganji",
    [
        (datetime(2024, 3, 15, 12, 0), "丁卯"),  # 卯月, 甲년 → 五虎遁
        (datetime(1985, 6, 23, 12, 0), "壬午"),
        (datetime(2024, 12, 25, 12, 0), "丙子"),
    ],
)
def test_wol_un(dt, ganji):
    p = sw.wol_un(dt)
    assert p.gan + p.ji == ganji


def test_wol_un_respects_jeolgi_boundary():
    # 입춘 직전/직후로 세운 년간이 바뀌어 월간도 달라진다 (연 경계)
    before = sw.wol_un(datetime(2024, 1, 20, 12, 0))  # 세운 2023(癸卯)
    after = sw.wol_un(datetime(2024, 2, 10, 12, 0))   # 세운 2024(甲辰)
    assert before.ji == "丑" and after.ji == "寅"
    assert before.gan != after.gan or before.ji != after.ji


# ── 일운 ──────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "d,ganji",
    [
        (date(1985, 6, 23), "癸巳"),
        (date(2000, 1, 7), "甲子"),
        (date(2024, 1, 1), "甲子"),
    ],
)
def test_il_un(d, ganji):
    p = sw.il_un(d)
    assert p.gan + p.ji == ganji


def test_il_un_accepts_datetime():
    assert sw.il_un(datetime(1985, 6, 23, 9, 0)).gan == "癸"


# ── 유효성·결정론 ─────────────────────────────────────────────
def test_all_valid_ganji():
    assert is_valid_ganji(*(lambda p: (p.gan, p.ji))(sw.se_un(1985)))
    assert is_valid_ganji(*(lambda p: (p.gan, p.ji))(sw.wol_un(datetime(1985, 6, 23, 12))))
    assert is_valid_ganji(*(lambda p: (p.gan, p.ji))(sw.il_un(date(1985, 6, 23))))


def test_deterministic():
    dt = datetime(1990, 9, 15, 8, 20)
    assert sw.wol_un(dt) == sw.wol_un(dt)
    assert sw.il_un(dt.date()) == sw.il_un(dt.date())

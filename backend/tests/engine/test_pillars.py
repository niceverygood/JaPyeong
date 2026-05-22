"""사주 4기둥 추출 모듈 검증 테스트 (TDD — 구현 전 작성). ★ 8자 100% 일치 요구.

설계: 일주(日柱)는 sxtwl(검증 완료: anchor 2000-01-07=甲子)로 산출,
년·월·시주 천간은 五虎遁(월)·五鼠遁(시) 명리 규칙으로 자체 계산.
진태양시·세수(입춘)·월경계(절)·일주변경(자정)·자시는 정책으로 통제.

주의: day 천간 oracle은 sxtwl. 정식 출시 전 자문위원 검증 케이스 100건 게이트 별도 유지.
"""

from dataclasses import replace

import pytest
import sxtwl

from src.engine import pillars as pl
from src.engine.constants import CHUN_GAN, JI_JI
from src.engine.policy import (
    DayChangePolicy,
    UnknownHourPolicy,
    get_default_policy,
)
from src.engine.schema import BirthInfo


def _birth(**kw) -> BirthInfo:
    base = dict(gender="M", calendar="solar", year=1985, month=6, day=23)
    base.update(kw)
    return BirthInfo(**base)


def test_full_chart_known_seoul():
    # 1985-06-23 14:30 서울. 진태양시 보정 후에도 未時.
    # 年 乙丑(1985), 月 壬午(乙년 午월 五虎遁), 日 癸巳(sxtwl), 時 己未(癸일 未시 五鼠遁)
    b = _birth(hour=14, minute=30, longitude=126.9784, latitude=37.5665)
    p = pl.build_pillars(b)
    assert (p.year.gan, p.year.ji) == ("乙", "丑")
    assert (p.month.gan, p.month.ji) == ("壬", "午")
    assert (p.day.gan, p.day.ji) == ("癸", "巳")
    assert (p.hour.gan, p.hour.ji) == ("己", "未")


@pytest.mark.parametrize(
    "hour,branch",
    [
        (23, "子"), (0, "子"), (1, "丑"), (2, "丑"), (3, "寅"), (5, "卯"),
        (7, "辰"), (9, "巳"), (11, "午"), (13, "未"), (15, "申"), (17, "酉"),
        (19, "戌"), (21, "亥"),
    ],
)
def test_hour_branch_mapping(hour, branch):
    # longitude 미지정 → 진태양시 보정 생략(시계시 그대로)으로 경계 명확화
    p = pl.build_pillars(_birth(hour=hour, minute=0))
    assert p.hour.ji == branch


def test_ipchun_year_flip():
    # 입춘 1985 = 02-04. 그 전은 1984(甲子), 후는 1985(乙丑)
    before = pl.build_pillars(_birth(month=2, day=1, hour=12))
    after = pl.build_pillars(_birth(month=2, day=10, hour=12))
    assert (before.year.gan, before.year.ji) == ("甲", "子")
    assert (after.year.gan, after.year.ji) == ("乙", "丑")


def test_midnight_day_change():
    # 자정(00:00) 일주변경(default). 23:30은 당일, 00:30은 익일 일주. 둘 다 子시.
    late = pl.build_pillars(_birth(month=6, day=23, hour=23, minute=30))
    early = pl.build_pillars(_birth(month=6, day=24, hour=0, minute=30))
    assert late.hour.ji == "子" and early.hour.ji == "子"
    # 06-23=癸巳, 06-24=甲午 (연속)
    assert (late.day.gan, late.day.ji) == ("癸", "巳")
    assert (early.day.gan, early.day.ji) == ("甲", "午")


def test_jasi_day_change_advances():
    pol = replace(get_default_policy(), day_change=DayChangePolicy.JASI)
    late = pl.build_pillars(_birth(month=6, day=23, hour=23, minute=30), policy=pol)
    # JASI: 23시는 익일(06-24=甲午) 일주로 넘어감
    assert (late.day.gan, late.day.ji) == ("甲", "午")


def test_hour_unknown_excluded():
    p = pl.build_pillars(_birth(hour=None))
    assert p.hour is None
    assert p.year is not None and p.month is not None and p.day is not None


def test_estimate_hour_not_implemented():
    pol = replace(get_default_policy(), unknown_hour=UnknownHourPolicy.ESTIMATE)
    with pytest.raises(NotImplementedError):
        pl.build_pillars(_birth(hour=None), policy=pol)


def test_lunar_input_matches_solar():
    # 양력 1985-06-23의 음력 표기를 구해 음력 입력으로 넣으면 동일 사주가 나와야 함
    sd = sxtwl.fromSolar(1985, 6, 23)
    ly, lm, ld = sd.getLunarYear(), sd.getLunarMonth(), sd.getLunarDay()
    is_leap = sd.isLunarLeap()
    solar_p = pl.build_pillars(_birth(hour=14, minute=30, longitude=126.9784))
    lunar_p = pl.build_pillars(
        _birth(calendar="lunar", year=ly, month=lm, day=ld,
               is_leap_month=is_leap, hour=14, minute=30, longitude=126.9784)
    )
    assert (lunar_p.day.gan, lunar_p.day.ji) == (solar_p.day.gan, solar_p.day.ji)
    assert (lunar_p.year.gan, lunar_p.month.gan) == (solar_p.year.gan, solar_p.month.gan)


def test_deterministic():
    b = _birth(hour=8, minute=15, longitude=128.6)
    a = pl.build_pillars(b)
    c = pl.build_pillars(b)
    assert (a.year, a.month, a.day, a.hour) == (c.year, c.month, c.day, c.hour)


def test_all_ganji_valid():
    # 임의 입력의 4기둥이 모두 유효한 60갑자 조합인지(천간/지지 음양 일치)
    from src.engine.ganji import is_valid_ganji

    p = pl.build_pillars(_birth(hour=14, minute=30, longitude=126.9784))
    for pillar in (p.year, p.month, p.day, p.hour):
        assert pillar.gan in CHUN_GAN and pillar.ji in JI_JI
        assert is_valid_ganji(pillar.gan, pillar.ji), f"{pillar.gan}{pillar.ji} 무효"

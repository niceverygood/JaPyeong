"""격국 모듈 검증 테스트 (잠정).

⚠ 자문위원 정책 7(GeokgukPriority) 미확정. TUCHUL_FIRST 통설 default 구현의
구조적 동작만 검증한다. 외격·잡기·합거는 다루지 않는다(자문위원 확정 후).
"""

import pytest

from src.engine import geokguk
from src.engine.schema import FourPillars, Pillar


def _p(g: str, j: str) -> Pillar:
    return Pillar(gan=g, ji=j)


def test_tuchul_match_in_month_gan():
    # 일간 甲, 월주 庚申 — 월지 申 정기 庚이 월간에 투출 → 편관격
    pillars = FourPillars(
        year=_p("丁", "卯"), month=_p("庚", "申"), day=_p("甲", "辰"), hour=_p("丙", "寅")
    )
    r = geokguk.determine_geokguk(pillars)
    assert r.name == "편관격"
    assert r.based_on == "transparent"
    assert r.transparent_position == "month_gan"
    assert r.confidence == "provisional"


def test_no_tuchul_falls_back_to_primary():
    # 월지 辰 지장간 {戊·癸·乙} 중 어느 것도 다른 천간(丁·丙·庚)에 없음 → 정기 戊 본기 → 편재격
    pillars = FourPillars(
        year=_p("丁", "卯"), month=_p("丙", "辰"), day=_p("甲", "子"), hour=_p("庚", "午")
    )
    r = geokguk.determine_geokguk(pillars)
    assert r.based_on == "primary"
    assert r.name == "편재격"  # 甲克戊 same eumyang → 편재


def test_geokguk_excludes_day_master_from_tuchul_check():
    # 일간 甲, 월주 庚寅 — 월지 寅 정기 甲(=dm, 투출 검사 제외).
    # 중기 丙·여기 戊 모두 다른 천간(丁·庚·癸)에 없음 → fallback 정기 甲 → 비견격
    pillars = FourPillars(
        year=_p("丁", "卯"), month=_p("庚", "寅"), day=_p("甲", "子"), hour=_p("癸", "酉")
    )
    r = geokguk.determine_geokguk(pillars)
    assert r.name == "비견격"
    assert r.based_on == "primary"


def test_returns_known_8_geokguk_or_bi_gyeop():
    # 결과 이름은 정해진 10종 격국 도메인 안 (정관/편관/정재/편재/정인/편인/식신/상관/비견/겁재)
    pillars = FourPillars(
        year=_p("丁", "卯"), month=_p("庚", "申"), day=_p("甲", "辰")
    )
    r = geokguk.determine_geokguk(pillars)
    assert r.name.endswith("격")
    assert r.name in geokguk.GEOKGUK_NAMES


def test_deterministic():
    pillars = FourPillars(
        year=_p("乙", "丑"), month=_p("壬", "午"), day=_p("丙", "戌"), hour=_p("乙", "未")
    )
    assert geokguk.determine_geokguk(pillars) == geokguk.determine_geokguk(pillars)


@pytest.mark.parametrize("hour", [None, _p("癸", "酉")])
def test_hour_optional(hour):
    pillars = FourPillars(
        year=_p("丁", "卯"), month=_p("庚", "申"), day=_p("甲", "辰"), hour=hour
    )
    r = geokguk.determine_geokguk(pillars)
    assert r.name in geokguk.GEOKGUK_NAMES

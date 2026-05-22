"""정책 기본값 가드.

이 테스트가 깨지면 default가 바뀐 것 → myeongri-policy.md 도 함께
수정했는지 확인해야 한다(SSOT 동기화).
"""

from dataclasses import replace

from src.engine.policy import (
    DaewoonCalc,
    DayChangePolicy,
    GeokgukPriority,
    JasiPolicy,
    LeapMonthPolicy,
    LunarInputPolicy,
    MyeongriPolicy,
    SesuPolicy,
    SinsalScope,
    SolarTimePolicy,
    UnknownHourPolicy,
    WoljuBoundaryPolicy,
    YongsinMethod,
    get_default_policy,
)


def test_default_policy_matches_documented_defaults():
    p = get_default_policy()
    assert p.solar_time == SolarTimePolicy.WITH_EOT
    assert p.jasi == JasiPolicy.UNIFIED
    assert p.sesu == SesuPolicy.IPCHUN
    assert p.wolju_boundary == WoljuBoundaryPolicy.JEOL
    assert p.leap_month == LeapMonthPolicy.BY_JEOLGI
    assert p.day_change == DayChangePolicy.MIDNIGHT
    assert p.geokguk_priority == GeokgukPriority.TUCHUL_FIRST
    assert p.yongsin_method == YongsinMethod.EOKBU
    assert p.sinsal_scope == SinsalScope.TWELVE_ONLY
    assert p.daewoon_calc == DaewoonCalc.DAYS_DIV3
    assert p.unknown_hour == UnknownHourPolicy.EXCLUDE
    assert p.lunar_input == LunarInputPolicy.ACCEPT


def test_policy_is_immutable():
    p = get_default_policy()
    try:
        p.solar_time = SolarTimePolicy.LONGITUDE_ONLY  # type: ignore[misc]
        raise AssertionError("frozen 정책이 수정됨")
    except AttributeError:
        pass  # frozen dataclass 기대 동작


def test_policy_override_via_replace():
    p = replace(get_default_policy(), solar_time=SolarTimePolicy.LONGITUDE_ONLY)
    assert p.solar_time == SolarTimePolicy.LONGITUDE_ONLY
    assert p.sesu == SesuPolicy.IPCHUN  # 나머지는 유지
    assert isinstance(p, MyeongriPolicy)

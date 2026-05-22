"""진태양시 보정 모듈 검증 테스트 (TDD — 구현 전 작성).

진태양시 = 지방평균시(경도차 보정) + 균시차(Equation of Time).
정책 SolarTimePolicy: LONGITUDE_ONLY(경도차만) / WITH_EOT(경도차+균시차, default).

표준자오선은 timezone의 해당 시점 UTC offset에서 도출(역사적 변경 자동 반영).
한국: 1954~1961 UTC+8:30(127.5°E), 그 외 UTC+9(135°E).

순수 결정론적: 같은 입력 → 항상 같은 출력.
"""

from datetime import datetime

import pytest

from src.engine import solar_time as st
from src.engine.policy import SolarTimePolicy, get_default_policy


def _replace_policy(solar_time_policy):
    from dataclasses import replace

    return replace(get_default_policy(), solar_time=solar_time_policy)


LON_ONLY = _replace_policy(SolarTimePolicy.LONGITUDE_ONLY)
WITH_EOT = _replace_policy(SolarTimePolicy.WITH_EOT)


def test_no_correction_at_standard_meridian():
    # 표준자오선(135°E, KST)·경도차만 → 보정 0
    dt = datetime(2000, 6, 21, 12, 0)
    corrected = st.correct_solar_time(dt, longitude=135.0, policy=LON_ONLY)
    assert corrected == dt


def test_seoul_longitude_only():
    # 서울 126.9784°E, 경도차만: (126.9784-135)*4 = -32.0864분
    dt = datetime(1985, 6, 23, 14, 30)
    corrected = st.correct_solar_time(dt, longitude=126.9784, policy=LON_ONLY)
    delta_sec = (corrected - dt).total_seconds()
    assert delta_sec == pytest.approx(-32.0864 * 60, abs=1.0)


def test_with_eot_differs_by_equation_of_time():
    dt = datetime(1985, 6, 23, 14, 30)
    lon = 126.9784
    only = st.correct_solar_time(dt, longitude=lon, policy=LON_ONLY)
    eot = st.correct_solar_time(dt, longitude=lon, policy=WITH_EOT)
    diff_min = (eot - only).total_seconds() / 60
    assert diff_min == pytest.approx(st.equation_of_time(dt), abs=1e-6)
    assert abs(diff_min) > 0.1  # 6월 하순 균시차는 0이 아님


@pytest.mark.parametrize(
    "date,expected_min",
    [
        (datetime(2001, 2, 11, 12, 0), -14.6),  # 2월 중순: 태양 느림(음)
        (datetime(2001, 11, 3, 12, 0), 16.3),  # 11월 초: 태양 빠름(양)
        (datetime(2001, 4, 15, 12, 0), 0.0),  # 4월 중순: 0 근처
    ],
)
def test_equation_of_time_reference_points(date, expected_min):
    assert st.equation_of_time(date) == pytest.approx(expected_min, abs=2.0)


def test_historical_meridian_changes():
    # 같은 경도라도 표준자오선이 달라지면(1955=127.5°E vs 1985=135°E) 보정량이 다르다.
    lon = 130.0
    d1955 = st.correct_solar_time(datetime(1955, 6, 1, 12, 0), longitude=lon, policy=LON_ONLY)
    d1985 = st.correct_solar_time(datetime(1985, 6, 1, 12, 0), longitude=lon, policy=LON_ONLY)
    off1955 = (d1955 - datetime(1955, 6, 1, 12, 0)).total_seconds()
    off1985 = (d1985 - datetime(1985, 6, 1, 12, 0)).total_seconds()
    assert off1955 != off1985


def test_deterministic():
    dt = datetime(1990, 9, 15, 8, 20)
    a = st.correct_solar_time(dt, longitude=128.6, policy=WITH_EOT)
    b = st.correct_solar_time(dt, longitude=128.6, policy=WITH_EOT)
    assert a == b


def test_returns_naive_datetime():
    dt = datetime(1985, 6, 23, 14, 30)
    corrected = st.correct_solar_time(dt, longitude=126.9784, policy=WITH_EOT)
    assert corrected.tzinfo is None

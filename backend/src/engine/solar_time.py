"""진태양시(眞太陽時) 보정.

명리에서 사주 시주(時柱)·일주(日柱) 경계는 출생지의 '실제 태양 위치'를 따르므로,
시계시(표준시)를 다음 두 가지로 보정한다.

  1. 경도차 보정(지방평균시): (출생지 경도 − 표준자오선) × 4분.
     표준자오선은 timezone의 해당 시점 UTC offset에서 도출한다(역사적 변경 자동 반영).
     예) 한국 1954~1961은 UTC+8:30(127.5°E), 그 외 UTC+9(135°E).
  2. 균시차(Equation of Time): 지구 공전 타원·자전축 경사로 생기는 ±16분 내 편차.
     SolarTimePolicy.WITH_EOT(default)일 때만 가산. LONGITUDE_ONLY면 생략.

균시차는 NOAA 계열 근사식(분 단위 정확)을 사용한다.
  TODO(policy): 균시차 포함 여부는 myeongri-policy.md 항목 1 — 자문위원 확정 필요.
  TODO: 한국 표준자오선 역사(1908년 이전 등)는 IANA tz(Asia/Seoul)에 의존.

순수 결정론적: 같은 입력 → 항상 같은 출력.
"""

import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.engine.policy import MyeongriPolicy, SolarTimePolicy, get_default_policy


def equation_of_time(dt: datetime) -> float:
    """균시차(분). 양수 = 진태양시가 평균태양시보다 빠름.

    근사식(NOAA 계열):
        B = 2π(N − 81) / 364,  N = 해당 연중 일수
        EoT = 9.87·sin(2B) − 7.53·cos(B) − 1.5·sin(B)   [분]
    분 단위 정확도(±~0.5분).
    """
    n = dt.timetuple().tm_yday
    b = 2 * math.pi * (n - 81) / 364
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def _standard_meridian_deg(dt: datetime, timezone: str) -> float:
    """timezone의 해당 시점 UTC offset(시간)으로부터 표준자오선(도)을 도출."""
    aware = dt.replace(tzinfo=ZoneInfo(timezone))
    offset = aware.utcoffset()
    if offset is None:  # pragma: no cover (유효 tz는 항상 offset 보유)
        raise ValueError(f"timezone offset 산출 불가: {timezone!r}")
    offset_hours = offset.total_seconds() / 3600
    return offset_hours * 15.0


def correct_solar_time(
    dt: datetime,
    longitude: float,
    policy: MyeongriPolicy | None = None,
    timezone: str = "Asia/Seoul",
) -> datetime:
    """시계시(naive 지방시) → 진태양시(naive 지방시)로 보정.

    Args:
        dt: 출생지 표준시 기준 naive datetime.
        longitude: 출생지 경도(°, 동경 +).
        policy: 정책. None이면 기본 정책(WITH_EOT).
        timezone: 출생지 IANA timezone (표준자오선 산출용).

    Returns:
        진태양시 naive datetime (동일 timezone의 태양시 시계값).
    """
    pol = policy or get_default_policy()

    meridian = _standard_meridian_deg(dt, timezone)
    longitude_minutes = (longitude - meridian) * 4.0

    eot_minutes = (
        equation_of_time(dt) if pol.solar_time == SolarTimePolicy.WITH_EOT else 0.0
    )

    return dt + timedelta(minutes=longitude_minutes + eot_minutes)

"""대운(大運) — 10년 단위 운의 흐름.

방향(순행/역행): 양남음녀(陽男陰女) 순행.
  - 년간이 양(陽)이고 남자, 또는 음(陰)이고 여자 → 순행(forward)
  - 그 외 → 역행(backward)

대운수(첫 대운 시작 나이): 출생 시각에서 절입(節入)까지의 일수 ÷ 3 (3일=1년).
  - 순행: 출생 후 다음 절(節)까지.
  - 역행: 출생 전 직전 절(節)부터.
  - DaewoonCalc.DAYS_DIV3 (default). 잔여는 반올림(round-half-up).
  TODO(policy): 잔여 처리·기준 시각(진태양시 vs 표준시)은 myeongri-policy.md
  항목 10 — 자문위원 확정 필요. 현재 effective_datetime(진태양시) 기준.

대운 간지: 月柱를 기준으로 순행이면 +1씩, 역행이면 -1씩 60갑자 진행.

순수 결정론적: 같은 입력(+같은 policy) → 항상 같은 출력.
"""

from dataclasses import dataclass
from datetime import datetime

from src.engine import jeolgi
from src.engine.constants import Eumyang
from src.engine.ganji import gan_eumyang, ganji_by_index, ganji_index
from src.engine.pillars import build_pillars, effective_datetime
from src.engine.policy import (
    DaewoonCalc,
    MyeongriPolicy,
    get_default_policy,
)
from src.engine.schema import BirthInfo


@dataclass(frozen=True, slots=True)
class DaewoonPeriod:
    """대운 한 주기(10년)."""

    sequence: int  # 1, 2, 3 …
    start_age: int  # 시작 나이
    gan: str
    ji: str


def daewoon_direction(year_gan: str, gender: str) -> str:
    """양남음녀 순행. 'forward' | 'backward'."""
    is_yang = gan_eumyang(year_gan) == Eumyang.YANG
    is_male = gender == "M"
    forward = (is_yang and is_male) or (not is_yang and not is_male)
    return "forward" if forward else "backward"


def _surrounding_jeol(dt: datetime, tz: str) -> tuple[datetime, datetime]:
    """dt를 둘러싼 직전 절·다음 절(節)의 절입 시각."""
    instants: list[datetime] = []
    for y in (dt.year - 1, dt.year, dt.year + 1):
        for p in jeolgi.solar_terms(y, tz):
            if p.is_jeol:
                instants.append(p.instant)
    instants = sorted(set(instants))
    prev_i = max(t for t in instants if t <= dt)
    next_i = min(t for t in instants if t > dt)
    return prev_i, next_i


def daewoon_start_age(birth: BirthInfo, policy: MyeongriPolicy | None = None) -> int:
    """대운수(첫 대운 시작 나이)."""
    pol = policy or get_default_policy()
    if pol.daewoon_calc != DaewoonCalc.DAYS_DIV3:
        raise NotImplementedError(
            f"대운 산출 정책 미지원: {pol.daewoon_calc} (현재 DAYS_DIV3만 구현)"
        )

    pillars = build_pillars(birth, pol)
    direction = daewoon_direction(pillars.year.gan, birth.gender)
    eff = effective_datetime(birth, pol)
    prev_jeol, next_jeol = _surrounding_jeol(eff, birth.timezone)

    if direction == "forward":
        diff_days = (next_jeol - eff).total_seconds() / 86400
    else:
        diff_days = (eff - prev_jeol).total_seconds() / 86400

    return int(diff_days / 3 + 0.5)  # round-half-up


def build_daewoon(
    birth: BirthInfo, policy: MyeongriPolicy | None = None, count: int = 9
) -> list[DaewoonPeriod]:
    """대운 목록(기본 9주기)."""
    pol = policy or get_default_policy()
    pillars = build_pillars(birth, pol)
    direction = daewoon_direction(pillars.year.gan, birth.gender)
    base_age = daewoon_start_age(birth, pol)

    month_index = ganji_index(pillars.month.gan, pillars.month.ji)
    step = 1 if direction == "forward" else -1

    periods: list[DaewoonPeriod] = []
    for k in range(1, count + 1):
        gan, ji = ganji_by_index(month_index + step * k)
        periods.append(
            DaewoonPeriod(
                sequence=k,
                start_age=base_age + 10 * (k - 1),
                gan=gan,
                ji=ji,
            )
        )
    return periods

"""사주 4기둥(년·월·일·시) 추출. ★ 8자 100% 일치 요구 모듈.

책임 분리(CLAUDE.md):
  - 일주(日柱): sxtwl로 해당 양력일의 60갑자 산출(검증 완료: anchor 2000-01-07=甲子).
  - 년·월·시주 천간: 五虎遁(월간)·五鼠遁(시간) 명리 규칙으로 자체 계산.
  - 진태양시·세수(입춘)·월경계(절)·일주변경 시점·자시 처리는 policy로 통제.

처리 흐름:
  1. 음력 입력이면 sxtwl로 양력 변환(LunarInputPolicy.ACCEPT).
  2. 출생지 경도가 있으면 진태양시 보정(solar_time). 없으면 시계시 사용.
  3. 보정 시각으로 세수(년)·월지(절)·일지(일주변경)·시지를 결정.
  4. 五虎遁/五鼠遁으로 월간·시간 산출, 년간은 1984甲子 anchor 기준.

정책 분기:
  - UnknownHourPolicy.ESTIMATE(시주 추정)는 미구현 → NotImplementedError.
  - DayChangePolicy.JASI(23시 일주변경) 지원, default는 MIDNIGHT(자정).

순수 결정론적: 같은 입력(+같은 policy) → 항상 같은 출력.
"""

from datetime import date, datetime, timedelta

import sxtwl

from src.engine import jeolgi
from src.engine.constants import CHUN_GAN, JI_JI
from src.engine.ganji import ganji_by_index
from src.engine.policy import (
    DayChangePolicy,
    LunarInputPolicy,
    MyeongriPolicy,
    UnknownHourPolicy,
    get_default_policy,
)
from src.engine.schema import BirthInfo, FourPillars, Pillar
from src.engine.solar_time import correct_solar_time

_YEAR_ANCHOR = 1984  # 1984년 = 甲子년 (년주 anchor)
_IN_INDEX = JI_JI.index("寅")  # 寅 = 2


def wuhudun_month_stem(year_gan: str, month_branch: str) -> str:
    """五虎遁: 년간 + 월지 → 월간.

    寅月 천간 = (2 + 2·(년간 index % 5)) % 10. 이후 월지 순서만큼 천간 진행.
    """
    yi = CHUN_GAN.index(year_gan)
    in_stem = (2 + 2 * (yi % 5)) % 10
    offset = (JI_JI.index(month_branch) - _IN_INDEX) % 12
    return CHUN_GAN[(in_stem + offset) % 10]


def wuseodun_hour_stem(day_gan: str, hour_branch_index: int) -> str:
    """五鼠遁: 일간 + 시지 → 시간.

    子時 천간 = (2·(일간 index % 5)) % 10. 시지 index(子=0)만큼 천간 진행.
    """
    di = CHUN_GAN.index(day_gan)
    ja_stem = (2 * (di % 5)) % 10
    return CHUN_GAN[(ja_stem + hour_branch_index) % 10]


def hour_branch_index(hour: int) -> int:
    """시각(0~23) → 시지 index(子=0 … 亥=11). 子시는 23~01시."""
    return ((hour + 1) // 2) % 12


def day_ganji(d: date) -> tuple[str, str]:
    """sxtwl로 해당 양력일의 일주(천간, 지지)."""
    sd = sxtwl.fromSolar(d.year, d.month, d.day)
    gz = sd.getDayGZ()
    return CHUN_GAN[gz.tg], JI_JI[gz.dz]


def effective_datetime(birth: BirthInfo, policy: MyeongriPolicy | None = None) -> datetime:
    """사주 산정에 쓰는 보정 시각(naive).

    음력→양력 변환 + (경도 있으면) 진태양시 보정까지 적용한 시각.
    시 미상이면 정오(12:00) 기준으로 날짜 경계만 안전 처리한다.
    대운수 산정 등에서 동일 기준 시각을 재사용한다.
    """
    pol = policy or get_default_policy()

    y, m, d = birth.year, birth.month, birth.day
    if birth.calendar == "lunar":
        if pol.lunar_input == LunarInputPolicy.REJECT:
            raise ValueError("음력 입력 비허용 정책(REJECT)")
        sd = sxtwl.fromLunar(y, m, d, birth.is_leap_month)
        y, m, d = sd.getSolarYear(), sd.getSolarMonth(), sd.getSolarDay()

    hour = birth.hour if birth.hour is not None else 12
    minute = birth.minute or 0
    civil = datetime(y, m, d, hour, minute)

    if birth.longitude is not None:
        return correct_solar_time(civil, birth.longitude, pol, birth.timezone)
    return civil


def build_pillars(birth: BirthInfo, policy: MyeongriPolicy | None = None) -> FourPillars:
    """출생 정보 → 사주 4기둥."""
    pol = policy or get_default_policy()

    # 시주 미상 처리
    hour_known = birth.hour is not None
    if not hour_known and pol.unknown_hour == UnknownHourPolicy.ESTIMATE:
        raise NotImplementedError("출생시 추정(ESTIMATE) 미구현 — 자문위원 정책 확정 필요")

    # 1~3. 보정 시각 (음력 변환 + 진태양시)
    eff = effective_datetime(birth, pol)

    # 4. 년주 (입춘 세수)
    syear = jeolgi.solar_year(eff, pol, birth.timezone)
    year_gan, year_ji = ganji_by_index((syear - _YEAR_ANCHOR) % 60)

    # 5. 월주 (절 경계 + 五虎遁)
    month_ji = jeolgi.month_branch_for(eff, pol, birth.timezone)
    month_gan = wuhudun_month_stem(year_gan, month_ji)

    # 6. 일주 (일주변경 정책 + sxtwl)
    day_date = eff.date()
    if pol.day_change == DayChangePolicy.JASI and eff.hour >= 23:
        day_date += timedelta(days=1)
    day_gan, day_ji = day_ganji(day_date)

    # 7. 시주 (五鼠遁)
    hour_pillar: Pillar | None = None
    if hour_known:
        hbi = hour_branch_index(eff.hour)
        hour_pillar = Pillar(gan=wuseodun_hour_stem(day_gan, hbi), ji=JI_JI[hbi])

    return FourPillars(
        year=Pillar(gan=year_gan, ji=year_ji),
        month=Pillar(gan=month_gan, ji=month_ji),
        day=Pillar(gan=day_gan, ji=day_ji),
        hour=hour_pillar,
    )

"""세운(歲運)·월운(月運)·일운(日運) — 흐르는 운.

- 세운: 명리 연도(입춘 세수)의 간지. 1984 甲子 anchor.
- 월운: 해당 시각의 절기 월지 + 세운 년간 五虎遁(pillars 재사용).
- 일운: 해당 양력일의 일주(sxtwl, 검증 완료).

기준값은 sxtwl getYearGZ/getMonthGZ/getDayGZ와 교차검증.
순수 결정론적: 같은 입력(+같은 policy) → 항상 같은 출력.
"""

from datetime import date, datetime

from src.engine import jeolgi
from src.engine.ganji import ganji_by_index
from src.engine.pillars import day_ganji, wuhudun_month_stem
from src.engine.policy import MyeongriPolicy, get_default_policy
from src.engine.schema import Pillar

_YEAR_ANCHOR = 1984  # 1984 = 甲子


def se_un(year: int) -> Pillar:
    """명리 연도(입춘 세수) 간지. year는 입춘이 지난 해의 연도."""
    gan, ji = ganji_by_index((year - _YEAR_ANCHOR) % 60)
    return Pillar(gan=gan, ji=ji)


def se_un_range(start_year: int, count: int = 10) -> list[tuple[int, Pillar]]:
    """연속 세운 목록 [(연도, 간지), ...]."""
    return [(start_year + i, se_un(start_year + i)) for i in range(count)]


def wol_un(dt: datetime, policy: MyeongriPolicy | None = None, tz: str = "Asia/Seoul") -> Pillar:
    """해당 시각의 월운(월간지). 절기 월지 + 세운 년간 五虎遁."""
    pol = policy or get_default_policy()
    syear = jeolgi.solar_year(dt, pol, tz)
    year_gan = se_un(syear).gan
    month_ji = jeolgi.month_branch_for(dt, pol, tz)
    return Pillar(gan=wuhudun_month_stem(year_gan, month_ji), ji=month_ji)


def il_un(d: date | datetime) -> Pillar:
    """해당 양력일의 일운(일주). datetime이면 날짜 부분만 사용."""
    if isinstance(d, datetime):
        d = d.date()
    gan, ji = day_ganji(d)
    return Pillar(gan=gan, ji=ji)

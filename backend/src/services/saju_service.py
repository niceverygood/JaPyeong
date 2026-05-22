"""사주 분석 서비스 — 엔진 모듈을 조합해 API 응답을 만든다.

엔진(룰베이스)과 API 사이의 비즈니스 로직 계층. LLM/RAG는 포함하지 않는다.
PII(출생정보)는 로그에 남기지 않는다.
"""

from datetime import date, datetime

from src.api.v1.saju_schemas import (
    DaewoonPeriodResponse,
    DaewoonResponse,
    FiveElementsResponse,
    LuckResponse,
    NatalResponse,
    RelationResponse,
)
from src.engine import five_elements as fe
from src.engine import jeolgi, sewoon
from src.engine import relations as rel
from src.engine.daewoon import build_daewoon, daewoon_direction, daewoon_start_age
from src.engine.ganji import gan_ohaeng
from src.engine.pillars import build_pillars
from src.engine.policy import MyeongriPolicy
from src.engine.schema import BirthInfo
from src.engine.ten_gods import count_ten_gods_in_pillars


def analyze_natal(birth: BirthInfo, policy: MyeongriPolicy | None = None) -> NatalResponse:
    pillars = build_pillars(birth, policy)
    day_master = pillars.day.gan

    ten = count_ten_gods_in_pillars(day_master, pillars, include_hidden=True)
    dist = fe.calculate_distribution(pillars, include_hidden=True)
    five = FiveElementsResponse(
        mok=dist.mok,
        hwa=dist.hwa,
        to=dist.to,
        geum=dist.geum,
        su=dist.su,
        total=dist.total,
        dominant=fe.get_dominant_element(dist).value,
        weakest=fe.get_weakest_element(dist).value,
        balance=round(fe.get_balance_score(dist), 4),
    )
    relations = [
        RelationResponse(type=r.type.value, members=list(r.members), positions=list(r.positions))
        for r in rel.find_all_relations(pillars)
    ]
    periods = [
        DaewoonPeriodResponse(sequence=p.sequence, start_age=p.start_age, gan=p.gan, ji=p.ji)
        for p in build_daewoon(birth, policy)
    ]
    daewoon = DaewoonResponse(
        direction=daewoon_direction(pillars.year.gan, birth.gender),
        start_age=daewoon_start_age(birth, policy),
        periods=periods,
    )

    return NatalResponse(
        pillars=pillars,
        day_master=day_master,
        day_master_element=gan_ohaeng(day_master).value,
        ten_gods=ten,
        five_elements=five,
        relations=relations,
        daewoon=daewoon,
    )


def luck_for(target: date, policy: MyeongriPolicy | None = None) -> LuckResponse:
    """특정 일자의 세운·월운·일운 (정오 기준)."""
    dt = datetime(target.year, target.month, target.day, 12, 0)
    return LuckResponse(
        date=target,
        se_un=sewoon.se_un(jeolgi.solar_year(dt, policy)),
        wol_un=sewoon.wol_un(dt, policy),
        il_un=sewoon.il_un(target),
    )

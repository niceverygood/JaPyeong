"""사주 분석 서비스 — 엔진 모듈을 조합해 API 응답을 만든다.

엔진(룰베이스)과 API 사이의 비즈니스 로직 계층. LLM/RAG는 포함하지 않는다.
PII(출생정보)는 로그에 남기지 않는다.
"""

from datetime import date, datetime

from src.api.v1.saju_schemas import (
    DaewoonPeriodResponse,
    DaewoonResponse,
    FiveElementsResponse,
    GeokgukResponse,
    LifeFlowPointResponse,
    LuckResponse,
    NatalResponse,
    RelationResponse,
    StrengthResponse,
    YongsinResponse,
)
from src.engine import five_elements as fe
from src.engine import geokguk as gk
from src.engine import jeolgi, life_flow, sewoon
from src.engine import relations as rel
from src.engine import strength as st
from src.engine import yongsin as ys
from src.engine.daewoon import build_daewoon, daewoon_direction, daewoon_start_age
from src.engine.ganji import gan_ohaeng
from src.engine.pillars import build_pillars
from src.engine.policy import MyeongriPolicy
from src.engine.schema import BirthInfo
from src.engine.ten_gods import TEN_GOD_HANJA, count_ten_gods_in_pillars


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
    daewoon_periods = build_daewoon(birth, policy)
    periods = [
        DaewoonPeriodResponse(sequence=p.sequence, start_age=p.start_age, gan=p.gan, ji=p.ji)
        for p in daewoon_periods
    ]
    daewoon = DaewoonResponse(
        direction=daewoon_direction(pillars.year.gan, birth.gender),
        start_age=daewoon_start_age(birth, policy),
        periods=periods,
    )

    # 출생시 미상 여부를 UI 표면화용 플래그로 전달(시주 pillar는 None으로 정확히 비워짐).
    # 강약 신뢰도 하향·note는 assess_strength가 hour=None을 보고 이미 처리하므로 중복 적용 금지.
    hour_estimated = birth.hour is None

    # ⚠ 잠정(provisional) — 자문위원 정책 7·8 미확정.
    strength = st.assess_strength(pillars)
    strength_dto = StrengthResponse(
        label=strength.label,
        ally_ratio=strength.ally_ratio,
        deuk_ryeong=strength.deuk_ryeong,
        deuk_ji=strength.deuk_ji,
        notes=list(strength.notes),
        confidence=strength.confidence,
    )
    geo = gk.determine_geokguk(pillars)
    geokguk_dto = GeokgukResponse(
        name=geo.name,
        ten_god=geo.ten_god.value,  # 한글 (e.g., "편관")
        based_on=geo.based_on,
        based_gan=geo.based_gan,
        special_pattern=geo.special_pattern,
        confidence=geo.confidence,
    )
    yong = ys.derive_yongsin(pillars)
    yongsin_dto = YongsinResponse(
        yongsin=yong.yongsin.value,
        huishin=yong.huishin.value,
        gisin=yong.gisin.value,
        gushin=yong.gushin.value,
        method=yong.method,
        based_on_strength=yong.based_on_strength,
        notes=list(yong.notes),
        confidence=yong.confidence,
    )
    _ = TEN_GOD_HANJA  # 추후 한자 병기에 사용

    # 인생 흐름 — 대운별 점수 (잠정)
    flow_points = life_flow.build_life_flow(pillars, daewoon_periods, yong)
    flow_dto = [
        LifeFlowPointResponse(
            sequence=p.sequence,
            start_age=p.start_age,
            end_age=p.end_age,
            gan=p.gan,
            ji=p.ji,
            gan_element=p.gan_element,
            ji_element=p.ji_element,
            score=p.score,
            label=p.label,
            reasons=list(p.reasons),
        )
        for p in flow_points
    ]

    return NatalResponse(
        pillars=pillars,
        day_master=day_master,
        day_master_element=gan_ohaeng(day_master).value,
        ten_gods=ten,
        five_elements=five,
        relations=relations,
        daewoon=daewoon,
        strength=strength_dto,
        geokguk=geokguk_dto,
        yongsin=yongsin_dto,
        life_flow=flow_dto,
        hour_estimated=hour_estimated,
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

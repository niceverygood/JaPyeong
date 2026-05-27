"""궁합(宮合) — 두 사주 간 결정론적 관계 분석.

LLM에 넘기기 전 룰베이스가 확정할 수 있는 신호만 추출한다:
  1. cross_relations  : 두 사주 천간/지지 간 합·충·형·해·파 (위치 표시)
  2. day_master_pair  : 두 일간의 십성 관계 (A→B, B→A)
  3. element_combined : 두 사주 오행 분포 합산 + 균형 점수
  4. element_dynamics : A 일간 vs B 우세 오행 (생/극/비화)
  5. element_balance_gain : 단독 vs 합산 균형 변화 (양수 = 보완)

학설 차가 큰 영역(일주 60갑자 궁합표, 신살 등)은 여기 포함하지 않고
LLM·자문위원 검증으로 미룬다. confidence: deterministic / heuristic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.engine import five_elements as fe
from src.engine import relations as rel
from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.schema import FourPillars
from src.engine.ten_gods import TenGod, get_ten_god


class ElementDynamic(StrEnum):
    """A → B 오행 작용 방향."""

    A_BIHWA_B = "비화"  # 같은 오행
    A_SAENG_B = "A생B"  # A가 B를 도움
    B_SAENG_A = "B생A"  # B가 A를 도움
    A_GEUK_B = "A극B"  # A가 B를 제어
    B_GEUK_A = "B극A"  # B가 A를 제어


@dataclass(frozen=True, slots=True)
class DayMasterPair:
    """두 일간의 십성 관계."""

    day_master_a: str  # 천간 (e.g., 丙)
    day_master_b: str
    element_a: Ohaeng
    element_b: Ohaeng
    a_to_b: TenGod  # A 입장에서 B 일간은 무엇인가
    b_to_a: TenGod
    dynamic: ElementDynamic


@dataclass(frozen=True, slots=True)
class ElementCombined:
    """두 사주 오행 분포 합산."""

    mok: float
    hwa: float
    to: float
    geum: float
    su: float
    total: float
    balance_a: float  # A 단독 균형 (0~1)
    balance_b: float  # B 단독 균형
    balance_combined: float  # 합산 균형
    balance_gain: float  # combined − max(a, b). 양수면 두 사주가 서로의 결손을 채움


@dataclass(frozen=True, slots=True)
class CompatibilityAnalysis:
    """궁합 결정론적 분석 결과."""

    cross_relations: list[rel.Relation]  # A↔B 합충형해파
    day_master_pair: DayMasterPair
    element_combined: ElementCombined
    strong_bonds_count: int  # 합 계열 cross 개수
    conflicts_count: int  # 충·형·해·파 cross 개수
    notes: list[str]  # 사람이 읽는 짧은 요약 신호 (LLM 보조용)


_SAENG_NEXT: dict[Ohaeng, Ohaeng] = {
    Ohaeng.MOK: Ohaeng.HWA,
    Ohaeng.HWA: Ohaeng.TO,
    Ohaeng.TO: Ohaeng.GEUM,
    Ohaeng.GEUM: Ohaeng.SU,
    Ohaeng.SU: Ohaeng.MOK,
}
_GEUK_NEXT: dict[Ohaeng, Ohaeng] = {
    Ohaeng.MOK: Ohaeng.TO,
    Ohaeng.HWA: Ohaeng.GEUM,
    Ohaeng.TO: Ohaeng.SU,
    Ohaeng.GEUM: Ohaeng.MOK,
    Ohaeng.SU: Ohaeng.HWA,
}

_HAP_TYPES = frozenset(
    {
        rel.RelationType.CHEON_GAN_HAP,
        rel.RelationType.JI_JI_YUK_HAP,
        rel.RelationType.JI_JI_SAM_HAP,
        rel.RelationType.JI_JI_BANG_HAP,
    }
)
_CONFLICT_TYPES = frozenset(
    {
        rel.RelationType.JI_JI_CHUNG,
        rel.RelationType.JI_JI_HYEONG,
        rel.RelationType.JI_JI_HAE,
        rel.RelationType.JI_JI_PA,
    }
)


def _element_dynamic(a: Ohaeng, b: Ohaeng) -> ElementDynamic:
    if a == b:
        return ElementDynamic.A_BIHWA_B
    if _SAENG_NEXT[a] == b:
        return ElementDynamic.A_SAENG_B
    if _SAENG_NEXT[b] == a:
        return ElementDynamic.B_SAENG_A
    if _GEUK_NEXT[a] == b:
        return ElementDynamic.A_GEUK_B
    if _GEUK_NEXT[b] == a:
        return ElementDynamic.B_GEUK_A
    raise AssertionError("오행 관계 누락")  # pragma: no cover


def _combine_distributions(
    dist_a: fe.FiveElementsDistribution, dist_b: fe.FiveElementsDistribution
) -> ElementCombined:
    """두 사주 오행 분포를 element-wise 합산하고 균형 점수를 비교."""
    combined = fe.FiveElementsDistribution(
        mok=dist_a.mok + dist_b.mok,
        hwa=dist_a.hwa + dist_b.hwa,
        to=dist_a.to + dist_b.to,
        geum=dist_a.geum + dist_b.geum,
        su=dist_a.su + dist_b.su,
        total=dist_a.total + dist_b.total,
    )
    ba = fe.get_balance_score(dist_a)
    bb = fe.get_balance_score(dist_b)
    bc = fe.get_balance_score(combined)
    return ElementCombined(
        mok=round(combined.mok, 4),
        hwa=round(combined.hwa, 4),
        to=round(combined.to, 4),
        geum=round(combined.geum, 4),
        su=round(combined.su, 4),
        total=round(combined.total, 4),
        balance_a=round(ba, 4),
        balance_b=round(bb, 4),
        balance_combined=round(bc, 4),
        balance_gain=round(bc - max(ba, bb), 4),
    )


def _build_notes(
    cross: list[rel.Relation],
    dmp: DayMasterPair,
    ec: ElementCombined,
) -> list[str]:
    """사람이 읽는 짧은 결정론적 신호 — LLM이 해석 시 참고."""
    notes: list[str] = []
    hap_n = sum(1 for r in cross if r.type in _HAP_TYPES)
    conflict_n = sum(1 for r in cross if r.type in _CONFLICT_TYPES)
    if hap_n:
        notes.append(f"두 사주 사이 합(合) 계열 관계가 {hap_n}건 검출됨.")
    if conflict_n:
        notes.append(f"두 사주 사이 충/형/해/파가 {conflict_n}건 검출됨.")
    # 일간 십성 — 십성 한글값을 그대로 노출
    notes.append(
        f"일간 관계: A({dmp.day_master_a}) 기준 B는 {dmp.a_to_b.value}, "
        f"B({dmp.day_master_b}) 기준 A는 {dmp.b_to_a.value}."
    )
    notes.append(f"오행 작용 방향: {dmp.dynamic.value}.")
    if ec.balance_gain > 0.05:
        notes.append(
            f"오행 균형이 합산 시 {ec.balance_gain:+.2f} 개선 — 서로의 결손을 채움."
        )
    elif ec.balance_gain < -0.05:
        notes.append(
            f"오행 균형이 합산 시 {ec.balance_gain:+.2f} 감소 — 한쪽으로 치우침."
        )
    return notes


def analyze_pair(
    pillars_a: FourPillars, pillars_b: FourPillars
) -> CompatibilityAnalysis:
    """두 사주의 결정론적 궁합 분석."""
    cross = rel.find_cross_relations(pillars_a, pillars_b)

    dm_a = pillars_a.day.gan
    dm_b = pillars_b.day.gan
    el_a = gan_ohaeng(dm_a)
    el_b = gan_ohaeng(dm_b)
    dmp = DayMasterPair(
        day_master_a=dm_a,
        day_master_b=dm_b,
        element_a=el_a,
        element_b=el_b,
        a_to_b=get_ten_god(dm_a, dm_b),
        b_to_a=get_ten_god(dm_b, dm_a),
        dynamic=_element_dynamic(el_a, el_b),
    )

    dist_a = fe.calculate_distribution(pillars_a, include_hidden=True)
    dist_b = fe.calculate_distribution(pillars_b, include_hidden=True)
    ec = _combine_distributions(dist_a, dist_b)

    notes = _build_notes(cross, dmp, ec)
    return CompatibilityAnalysis(
        cross_relations=cross,
        day_master_pair=dmp,
        element_combined=ec,
        strong_bonds_count=sum(1 for r in cross if r.type in _HAP_TYPES),
        conflicts_count=sum(1 for r in cross if r.type in _CONFLICT_TYPES),
        notes=notes,
    )

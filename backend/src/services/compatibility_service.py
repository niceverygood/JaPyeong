"""궁합 분석 서비스 — 두 사주 결정론 + DTO 직렬화 (LLM은 별도).

엔진(compatibility)과 API 사이의 비즈니스 로직 계층. PII는 로그에 남기지 않는다.
"""

from __future__ import annotations

from src.api.v1.compat_schemas import (
    CompatAnalysisDTO,
    DayMasterPairDTO,
    ElementCombinedDTO,
)
from src.api.v1.saju_schemas import RelationResponse
from src.engine import compatibility as compat
from src.engine.pillars import build_pillars
from src.engine.policy import MyeongriPolicy
from src.engine.schema import BirthInfo, FourPillars


def analyze_pair(
    birth_a: BirthInfo,
    birth_b: BirthInfo,
    policy: MyeongriPolicy | None = None,
) -> tuple[FourPillars, FourPillars, CompatAnalysisDTO]:
    """두 출생정보 → 사주 8자 두 벌 + 결정론적 궁합 분석 DTO."""
    pa = build_pillars(birth_a, policy)
    pb = build_pillars(birth_b, policy)
    res = compat.analyze_pair(pa, pb)

    return pa, pb, CompatAnalysisDTO(
        cross_relations=[
            RelationResponse(
                type=r.type.value,
                members=list(r.members),
                positions=list(r.positions),
            )
            for r in res.cross_relations
        ],
        day_master_pair=DayMasterPairDTO(
            day_master_a=res.day_master_pair.day_master_a,
            day_master_b=res.day_master_pair.day_master_b,
            element_a=res.day_master_pair.element_a.value,
            element_b=res.day_master_pair.element_b.value,
            a_to_b=res.day_master_pair.a_to_b.value,
            b_to_a=res.day_master_pair.b_to_a.value,
            dynamic=res.day_master_pair.dynamic.value,
        ),
        element_combined=ElementCombinedDTO(
            mok=res.element_combined.mok,
            hwa=res.element_combined.hwa,
            to=res.element_combined.to,
            geum=res.element_combined.geum,
            su=res.element_combined.su,
            total=res.element_combined.total,
            balance_a=res.element_combined.balance_a,
            balance_b=res.element_combined.balance_b,
            balance_combined=res.element_combined.balance_combined,
            balance_gain=res.element_combined.balance_gain,
        ),
        strong_bonds_count=res.strong_bonds_count,
        conflicts_count=res.conflicts_count,
        notes=list(res.notes),
    )

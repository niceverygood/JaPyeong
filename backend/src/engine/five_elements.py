"""오행(五行) 분포 — 사주 8자 + 지장간의 오행 가중치 집계.

TODO(policy): 향후 ElementWeightPolicy로 policy.py 통합 가능.
  현재 default는 자평진전 계열 보수값(특정 유파의 확정 정책 아님).
  오행 가중치(천간 vs 지장간 비중, 통근 가산)는 유파 차이가 큰 영역이므로
  ElementWeights를 외부 주입 가능하게 둔다.

신강신약(strength)·용신(yongsin)이 이 분포에 직접 의존한다.
순수 결정론적: 같은 입력(+같은 weights) → 항상 같은 출력.
"""

import math
from dataclasses import dataclass, field

from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.jijanggan import StageType, get_jijanggan
from src.engine.schema import FourPillars

# 오행 정렬 순서(동률 시 tie-break 기준): 木火土金水
ELEMENT_ORDER: tuple[Ohaeng, ...] = (
    Ohaeng.MOK,
    Ohaeng.HWA,
    Ohaeng.TO,
    Ohaeng.GEUM,
    Ohaeng.SU,
)


@dataclass(frozen=True, slots=True)
class ElementWeights:
    """오행 기여 가중치. default는 보수값(정책 아님)."""

    stem_weight: float = 1.0
    branch_primary_weight: float = 1.0  # 지장간 正氣
    branch_middle_weight: float = 0.5  # 中氣
    branch_residual_weight: float = 0.3  # 餘氣


@dataclass(frozen=True, slots=True)
class Contribution:
    """오행 기여 한 건 (출처 추적용)."""

    source: str  # "year_gan" | "month_ji_primary" | "day_ji_middle" ...
    element: Ohaeng
    weight: float


@dataclass(frozen=True, slots=True)
class FiveElementsDistribution:
    """오행 분포 결과."""

    mok: float
    hwa: float
    to: float
    geum: float
    su: float
    total: float
    breakdown: dict[str, list[Contribution]] = field(default_factory=dict)

    def by_element(self, element: Ohaeng) -> float:
        return {
            Ohaeng.MOK: self.mok,
            Ohaeng.HWA: self.hwa,
            Ohaeng.TO: self.to,
            Ohaeng.GEUM: self.geum,
            Ohaeng.SU: self.su,
        }[element]


_POSITIONS = ("year", "month", "day", "hour")
_STAGE_SUFFIX = {
    StageType.JEONGGI: "primary",
    StageType.JUNGGI: "middle",
    StageType.YEOGI: "residual",
}


def calculate_distribution(
    pillars: FourPillars,
    include_hidden: bool = True,
    weights: ElementWeights | None = None,
) -> FiveElementsDistribution:
    """사주 오행 분포 계산.

    - 천간 4개(년월일시, 일간 포함): stem_weight.
    - include_hidden=False: 각 지지의 正氣(본기)만 branch_primary_weight로 가산.
    - include_hidden=True: 지장간 전부(正氣/中氣/餘氣)를 각 가중치로 가산.
    - 시주(hour)가 없으면 해당 기여를 제외.
    """
    w = weights or ElementWeights()
    sums: dict[Ohaeng, float] = dict.fromkeys(ELEMENT_ORDER, 0.0)
    breakdown: dict[str, list[Contribution]] = {e.value: [] for e in ELEMENT_ORDER}

    def add(source: str, element: Ohaeng, weight: float) -> None:
        sums[element] += weight
        breakdown[element.value].append(Contribution(source, element, weight))

    for pos in _POSITIONS:
        pillar = getattr(pillars, pos, None)
        if pillar is None:
            continue
        add(f"{pos}_gan", gan_ohaeng(pillar.gan), w.stem_weight)

        hidden = get_jijanggan(pillar.ji)
        for h in hidden:
            if not include_hidden and h.stage != StageType.JEONGGI:
                continue
            if h.stage == StageType.JEONGGI:
                weight = w.branch_primary_weight
            elif h.stage == StageType.JUNGGI:
                weight = w.branch_middle_weight
            else:
                weight = w.branch_residual_weight
            add(f"{pos}_ji_{_STAGE_SUFFIX[h.stage]}", gan_ohaeng(h.gan), weight)

    total = sum(sums.values())
    return FiveElementsDistribution(
        mok=sums[Ohaeng.MOK],
        hwa=sums[Ohaeng.HWA],
        to=sums[Ohaeng.TO],
        geum=sums[Ohaeng.GEUM],
        su=sums[Ohaeng.SU],
        total=total,
        breakdown=breakdown,
    )


def get_dominant_element(dist: FiveElementsDistribution) -> Ohaeng:
    """최대 비중 오행. 동률이면 木火土金水 순으로 앞선 것."""
    return max(ELEMENT_ORDER, key=lambda e: (dist.by_element(e), -ELEMENT_ORDER.index(e)))


def get_weakest_element(dist: FiveElementsDistribution) -> Ohaeng:
    """최소 비중 오행. 동률이면 木火土金水 순으로 앞선 것."""
    return min(ELEMENT_ORDER, key=lambda e: (dist.by_element(e), ELEMENT_ORDER.index(e)))


def get_balance_score(dist: FiveElementsDistribution) -> float:
    """오행 균형도 0~1 (1=완벽 균형, 0=한 오행 집중).

    공식: 5개 오행 비율 p_i에 대한 정규화 섀넌 엔트로피.
        score = (-Σ p_i ln p_i) / ln(5)
    p_i=0 항은 0으로 처리. total<=0이면 0.0.
    완벽 균등(각 0.2) → ln5/ln5 = 1, 단일 오행 → 0.
    """
    if dist.total <= 0:
        return 0.0
    entropy = 0.0
    for e in ELEMENT_ORDER:
        p = dist.by_element(e) / dist.total
        if p > 0:
            entropy -= p * math.log(p)
    return entropy / math.log(len(ELEMENT_ORDER))

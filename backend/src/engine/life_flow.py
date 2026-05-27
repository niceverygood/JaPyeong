"""인생 흐름 — 대운 80년치 결정론적 길흉 스코어.

⚠ 잠정(provisional). 점수의 절대값은 의미 작고, **상대적 흐름** 시각화용.
   자문위원 확정 전이며 학파(특히 조후·통관 우선 시) 견해 차이 있음.

스코어 (-5..+5):
  - 대운 천간 오행이 용신과 같음: +2
  - 대운 지지 본기가 용신과 같음: +2
  - 대운 천간/지지가 희신: +1
  - 대운 천간/지지가 기신: -2
  - 대운 천간/지지가 구신: -1
  - 대운 지지가 일지(natal day_ji) 와 충: -1
  - 대운 지지가 일지와 합(육/삼/방): +0.5 (양 측 합산 가능)

총합 [-5, +5] 클램프. label: '대길/길/평/주의/흉'.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.engine import relations as rel
from src.engine.constants import Ohaeng
from src.engine.daewoon import DaewoonPeriod
from src.engine.ganji import gan_ohaeng
from src.engine.jijanggan import get_primary_stem
from src.engine.schema import FourPillars
from src.engine.yongsin import YongsinResult


@dataclass(frozen=True, slots=True)
class LifeFlowPoint:
    """대운 1주기의 점수와 라벨."""

    sequence: int
    start_age: int
    end_age: int
    gan: str
    ji: str
    gan_element: str  # 木火土金水 (한자)
    ji_element: str  # 지지 본기 오행
    score: float
    label: str  # 대길/길/평/주의/흉
    reasons: list[str]


_LABEL_THRESHOLDS = (
    (3.0, "대길"),
    (1.5, "길"),
    (-1.5, "평"),
    (-3.0, "주의"),
    (-5.0, "흉"),
)


def _label_for(score: float) -> str:
    for threshold, label in _LABEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "흉"


_HAP_TYPES = frozenset(
    {
        rel.RelationType.JI_JI_YUK_HAP,
        rel.RelationType.JI_JI_SAM_HAP,
        rel.RelationType.JI_JI_BANG_HAP,
    }
)


def _ji_hap_chung_score(
    daewoon_ji: str, natal_day_ji: str
) -> tuple[float, list[str]]:
    """대운 지지와 사주 일지의 합/충 점수."""
    if daewoon_ji == natal_day_ji:
        return 0.0, []
    pair = frozenset((daewoon_ji, natal_day_ji))
    score = 0.0
    reasons: list[str] = []
    # 충
    chung_pairs = [
        frozenset((a, b))
        for a, b in [
            ("子", "午"),
            ("丑", "未"),
            ("寅", "申"),
            ("卯", "酉"),
            ("辰", "戌"),
            ("巳", "亥"),
        ]
    ]
    if pair in chung_pairs:
        score -= 1.0
        reasons.append(f"일지({natal_day_ji})와 충(沖)")
    # 육합
    yukhap_pairs = [
        frozenset((a, b))
        for a, b in [
            ("子", "丑"),
            ("寅", "亥"),
            ("卯", "戌"),
            ("辰", "酉"),
            ("巳", "申"),
            ("午", "未"),
        ]
    ]
    if pair in yukhap_pairs:
        score += 0.5
        reasons.append(f"일지({natal_day_ji})와 육합")
    return score, reasons


def _element_score(
    element: Ohaeng, yongsin: YongsinResult, source_label: str
) -> tuple[float, str | None]:
    if element == yongsin.yongsin:
        return 2.0, f"{source_label}={element.value} 용신"
    if element == yongsin.huishin:
        return 1.0, f"{source_label}={element.value} 희신"
    if element == yongsin.gisin:
        return -2.0, f"{source_label}={element.value} 기신"
    if element == yongsin.gushin:
        return -1.0, f"{source_label}={element.value} 구신"
    return 0.0, None


def score_period(
    period: DaewoonPeriod,
    pillars: FourPillars,
    yongsin: YongsinResult,
) -> LifeFlowPoint:
    """대운 1주기를 [-5, +5] 점수로."""
    gan_el = gan_ohaeng(period.gan)
    ji_primary = get_primary_stem(period.ji)
    ji_el = gan_ohaeng(ji_primary)

    score = 0.0
    reasons: list[str] = []

    sg, reason = _element_score(gan_el, yongsin, "대운 천간")
    score += sg
    if reason:
        reasons.append(reason)

    sj, reason = _element_score(ji_el, yongsin, "대운 지지")
    score += sj
    if reason:
        reasons.append(reason)

    # 일지와의 합/충
    s2, r2 = _ji_hap_chung_score(period.ji, pillars.day.ji)
    score += s2
    reasons.extend(r2)

    # 클램프
    score = max(-5.0, min(5.0, score))
    return LifeFlowPoint(
        sequence=period.sequence,
        start_age=period.start_age,
        end_age=period.start_age + 9,
        gan=period.gan,
        ji=period.ji,
        gan_element=gan_el.value,
        ji_element=ji_el.value,
        score=round(score, 2),
        label=_label_for(score),
        reasons=reasons,
    )


def build_life_flow(
    pillars: FourPillars,
    daewoon_periods: list[DaewoonPeriod],
    yongsin: YongsinResult,
) -> list[LifeFlowPoint]:
    return [score_period(p, pillars, yongsin) for p in daewoon_periods]

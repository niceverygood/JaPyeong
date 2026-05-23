"""신강신약(身强身弱) — 일간의 강약 평가. ⚠ 잠정(provisional).

근거(통설, myeongri-policy.md 항목 8 default `EOKBU` 위에서 동작):
  - 아군(同氣·印星) 비율로 신강/신약 판단.
  - 득령(得令): 월지 본기 오행이 아군이면 True.
  - 득지(得地): 일지 본기 오행이 아군이면 True.
  - 임계값(잠정): ally_ratio >= 0.55 → 신강 / <= 0.40 → 신약 / 그 사이 → 중화.

⚠ 자문위원 정책 8(YongsinMethod) 확정 + 검증 케이스 50건+ 전까지는 모든
출력에 confidence = "provisional"을 부여한다. 시그니처는 유지하며
정밀 구현 시 내부만 교체할 수 있도록 책임을 분리한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.engine import five_elements as fe
from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.jijanggan import get_primary_stem
from src.engine.schema import FourPillars

StrengthLabel = Literal["신강", "신약", "중화"]

# 잠정 임계값 — 자문위원 확정 시 정밀 조정.
SIN_GANG_THRESHOLD = 0.55
SIN_YAK_THRESHOLD = 0.40

# 오행 상생: a 가 生하는 오행 (자식)
_SAENG_NEXT: dict[Ohaeng, Ohaeng] = {
    Ohaeng.MOK: Ohaeng.HWA,
    Ohaeng.HWA: Ohaeng.TO,
    Ohaeng.TO: Ohaeng.GEUM,
    Ohaeng.GEUM: Ohaeng.SU,
    Ohaeng.SU: Ohaeng.MOK,
}


def _parent_ohaeng(child: Ohaeng) -> Ohaeng:
    """자식 오행 → 부모(生하는 쪽) 오행. 일간을 生하는 인성."""
    for parent, descendant in _SAENG_NEXT.items():
        if descendant is child:
            return parent
    raise AssertionError("오행 상생 정의 누락")  # pragma: no cover


@dataclass(frozen=True, slots=True)
class StrengthResult:
    """신강신약 평가."""

    label: StrengthLabel
    ally_ratio: float  # 아군 점수 / 총합 (0~1)
    deuk_ryeong: bool  # 득령(월지)
    deuk_ji: bool  # 득지(일지)
    ally_score: float
    hostile_score: float
    total_score: float
    ally_elements: tuple[Ohaeng, Ohaeng]  # (same, parent)
    notes: tuple[str, ...] = ()
    confidence: str = "provisional"
    breakdown: dict[str, float] = field(default_factory=dict)


def assess_strength(pillars: FourPillars) -> StrengthResult:
    """사주 → 신강신약. 잠정 통설 기준."""
    dm = pillars.day.gan
    dm_oh = gan_ohaeng(dm)
    parent_oh = _parent_ohaeng(dm_oh)
    allies = (dm_oh, parent_oh)

    dist = fe.calculate_distribution(pillars, include_hidden=True)
    breakdown = {
        Ohaeng.MOK.value: dist.mok,
        Ohaeng.HWA.value: dist.hwa,
        Ohaeng.TO.value: dist.to,
        Ohaeng.GEUM.value: dist.geum,
        Ohaeng.SU.value: dist.su,
    }
    ally_score = dist.by_element(dm_oh) + dist.by_element(parent_oh)
    total = dist.total
    hostile_score = total - ally_score
    ratio = (ally_score / total) if total > 0 else 0.0

    if ratio >= SIN_GANG_THRESHOLD:
        label: StrengthLabel = "신강"
    elif ratio <= SIN_YAK_THRESHOLD:
        label = "신약"
    else:
        label = "중화"

    month_primary_oh = gan_ohaeng(get_primary_stem(pillars.month.ji))
    day_primary_oh = gan_ohaeng(get_primary_stem(pillars.day.ji))
    deuk_ryeong = month_primary_oh in allies
    deuk_ji = day_primary_oh in allies

    notes: list[str] = []
    if deuk_ryeong:
        notes.append("득령(월지 본기가 아군)")
    if deuk_ji:
        notes.append("득지(일지 본기가 아군)")

    return StrengthResult(
        label=label,
        ally_ratio=round(ratio, 4),
        deuk_ryeong=deuk_ryeong,
        deuk_ji=deuk_ji,
        ally_score=round(ally_score, 4),
        hostile_score=round(hostile_score, 4),
        total_score=round(total, 4),
        ally_elements=allies,
        notes=tuple(notes),
        breakdown=breakdown,
    )

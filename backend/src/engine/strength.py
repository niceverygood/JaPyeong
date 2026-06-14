"""신강신약(身强身弱) — 일간의 강약 평가.

근거(통설):
  - 월령(月令) 지배: 월지가 신강약의 최대 변수다. 지지 기여에 위치 가중을 주어
    월지 ×3, 일지 ×2, 년지·시지 ×1 로 집계한다(득령이 신강을 좌우하도록).
  - 아군(同氣 비겁 + 印星) 가중 비율로 신강/신약 판단.
  - 득령(得令): 월지 본기 오행이 아군이면 True (위치 가중으로 점수에도 강하게 반영).
  - 득지(得地): 일지 본기 오행이 아군이면 True.
  - 통근(通根): 일간 오행/인성이 지지 지장간에 뿌리내림 — 위치 가중 분포에 반영됨.

이전 결함(동일 가중)으로 일간 甲·월지 寅(건록·득령) 명조가 신약으로 오판되던 문제를
월령 위치 가중으로 해소했다. 임계값은 골든 검증셋으로 보정한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.engine import five_elements as fe
from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.jijanggan import get_jijanggan, get_primary_stem
from src.engine.schema import FourPillars

StrengthLabel = Literal["신강", "신약", "중화"]

# 지지 위치 가중 — 월령(月令) 지배. 통설: 월지가 강약의 최대 변수.
BRANCH_POSITION_WEIGHTS: dict[str, float] = {
    "month": 3.0,
    "day": 2.0,
    "year": 1.0,
    "hour": 1.0,
}

# 위치 가중 분포 기준 임계값(골든셋 보정값). 아군=비겁+인성(5오행 중 2).
SIN_GANG_THRESHOLD = 0.50
SIN_YAK_THRESHOLD = 0.32

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

    # 월령 지배 — 지지 기여에 위치 가중을 주어 집계.
    dist = fe.calculate_distribution(
        pillars, include_hidden=True, position_weights=BRANCH_POSITION_WEIGHTS
    )
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

    # 통근(通根): 일간 오행/인성이 지지 지장간에 뿌리내리는가 (위치 가중 분포에 이미 반영).
    tonggeun = False
    for pos in ("year", "month", "day", "hour"):
        pillar = getattr(pillars, pos, None)
        if pillar is None:
            continue
        if any(gan_ohaeng(h.gan) in allies for h in get_jijanggan(pillar.ji)):
            tonggeun = True
            break

    notes: list[str] = []
    if deuk_ryeong:
        notes.append("득령(월지 본기가 아군)")
    if deuk_ji:
        notes.append("득지(일지 본기가 아군)")
    if tonggeun:
        notes.append("통근(일간이 지지에 뿌리)")
    notes.append("월령 위치 가중 적용(월지×3·일지×2)")

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

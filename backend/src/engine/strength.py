"""신강신약(身强身弱) — 일간의 강약 평가.

근거(통설):
  - 월령(月令) 지배: 월지가 신강약의 최대 변수다. 위치 배점에서 월지를 가장 크게
    두고(월지 40 vs 천간 8~12), 득령이 강약을 강하게 끌어당기도록 한다.
  - 지지 배점 분할: 임의 비율이 아니라 월률분야(月律分野) 일수(jijanggan.days, 합 30)
    비례로 본기·중기·여기에 나눈다 — 명리 통설(월률분야)에 직접 근거를 둔다.
  - 아군(同氣 비겁 + 印星) 가중 비율로 신강/신약 판단.
  - 득령(得令): 월지 본기 오행이 아군이면 True. 득지(得地): 일지 본기가 아군이면 True.
  - 통근(通根): 일간/인성이 어느 지지의 '본기'에 뿌리내리면 True(약한 여기 뿌리는 제외).

임계값 보정: 아군은 5오행 중 2개(비겁+인성)라 균등 분포의 자연 비율이 0.40이다.
따라서 중화 기준을 0.40에 두고 신강 ≥0.45 / 신약 ≤0.35 로 대칭 배치한다
(이전 0.50/0.40은 균등 명조를 신약으로 오판하는 편향이 있었다). 골든 검증셋으로 확인.

주의: 월령 본기는 압도적이나 단독으로 신강을 '보장'하지는 않는다 — 건록·득령이라도
관살·식상이 태왕하면 신약일 수 있다(이는 통설에 부합하는 정상 동작).
시주(時) 미상이면 분포 정규화가 흔들려 라벨이 바뀔 수 있어 신뢰도를 한 단계 낮춘다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.jijanggan import get_jijanggan, get_primary_stem
from src.engine.schema import FourPillars

StrengthLabel = Literal["신강", "신약", "중화"]

# 학술파 計分法 위치 배점 — 천간4 + 지지본기4, 합 ~120. 월지(月令)가 압도(40).
POS_WEIGHT: dict[str, float] = {
    "year_gan": 8.0, "month_gan": 12.0, "day_gan": 12.0, "hour_gan": 12.0,
    "year_ji": 4.0, "month_ji": 40.0, "day_ji": 12.0, "hour_ji": 12.0,
}
# 임계값: 균등 분포 자연 비율 0.40을 중화 중심에 두고 ±0.05 대칭.
SIN_GANG_THRESHOLD = 0.45
SIN_YAK_THRESHOLD = 0.35
NEUTRAL_CENTER = 0.40  # 중화대 중심(아군 5오행 중 2개 = 0.40)
# 월지 본기가 비겁(건록·양인격)일 때만 득령 보너스.
DEUK_RYEONG_BONUS = 0.03
# 신뢰도 등급: 신강/신약은 '경계 너머 거리', 중화는 '중심 근접도'로 등급화.
#   high=명백 / medium=보통 / low=경계 근처(유파 따라 갈릴 수 있음).
#   '정직한 불확실성 표면화' — 경계 명조는 low로 표기해 과신을 피한다.
CONF_HIGH_MARGIN = 0.08
CONF_MEDIUM_MARGIN = 0.03
# 중화 전용(밴드 폭 0.10이라 별도 척도): 중심서 가까울수록 확실한 중화.
CONF_NEUTRAL_HIGH = 0.03   # |ratio-0.40| ≤ 0.02 → high (거의 정중앙)
CONF_NEUTRAL_MEDIUM = 0.01

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


def _grade(margin: float, high: float, medium: float) -> str:
    """거리(margin)를 high/medium/low 신뢰도로 등급화."""
    if margin >= high:
        return "high"
    if margin >= medium:
        return "medium"
    return "low"


def _downgrade(confidence: str) -> str:
    """신뢰도를 한 단계 낮춤(시주 미상 등 불확실 가산)."""
    return {"high": "medium", "medium": "low", "low": "low"}.get(confidence, "low")


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
    """사주 → 신강신약. 위치 배점 計分法으로 일간 아군 비율을 산정.

    아군 = 비겁(同氣, 일간 오행) + 인성(生我, 부모 오행).
    각 위치에 고정 배점(POS_WEIGHT)을 두고, 지지 배점은 지장간을 월률분야 일수(days)
    비례로 분할한다(임의 비율이 아니라 통설 월률분야에 직접 근거).
    월지(月令) 배점이 40으로 가장 크지만, 단독으로 신강을 '보장'하지는 않는다.
    """
    dm = pillars.day.gan
    dm_oh = gan_ohaeng(dm)
    parent_oh = _parent_ohaeng(dm_oh)
    allies = (dm_oh, parent_oh)
    ally_set = {dm_oh, parent_oh}

    elem_sum: dict[Ohaeng, float] = dict.fromkeys(
        (Ohaeng.MOK, Ohaeng.HWA, Ohaeng.TO, Ohaeng.GEUM, Ohaeng.SU), 0.0
    )
    ally_score = 0.0
    total = 0.0
    has_hour = getattr(pillars, "hour", None) is not None

    for pos in ("year", "month", "day", "hour"):
        pillar = getattr(pillars, pos, None)
        if pillar is None:
            continue
        # 천간
        gw = POS_WEIGHT[f"{pos}_gan"]
        g_oh = gan_ohaeng(pillar.gan)
        total += gw
        elem_sum[g_oh] += gw
        if g_oh in ally_set:
            ally_score += gw
        # 지지 — 배점을 지장간 월률분야 일수(days, 합 30) 비례로 분할
        bw = POS_WEIGHT[f"{pos}_ji"]
        hs = get_jijanggan(pillar.ji)
        norm = sum(h.days for h in hs) or 1
        for h in hs:
            piece = bw * h.days / norm
            h_oh = gan_ohaeng(h.gan)
            total += piece
            elem_sum[h_oh] += piece
            if h_oh in ally_set:
                ally_score += piece

    ratio = (ally_score / total) if total > 0 else 0.0

    month_primary_oh = gan_ohaeng(get_primary_stem(pillars.month.ji))
    day_primary_oh = gan_ohaeng(get_primary_stem(pillars.day.ji))
    deuk_ryeong = month_primary_oh in ally_set
    deuk_ji = day_primary_oh in ally_set

    # 득령 보너스: 월지 본기가 '비겁'(건록·양인격)일 때만 — 인성 득령엔 미적용.
    if month_primary_oh == dm_oh:
        ratio = min(1.0, ratio + DEUK_RYEONG_BONUS)

    if ratio >= SIN_GANG_THRESHOLD:
        label: StrengthLabel = "신강"
        confidence = _grade(ratio - SIN_GANG_THRESHOLD, CONF_HIGH_MARGIN, CONF_MEDIUM_MARGIN)
    elif ratio <= SIN_YAK_THRESHOLD:
        label = "신약"
        confidence = _grade(SIN_YAK_THRESHOLD - ratio, CONF_HIGH_MARGIN, CONF_MEDIUM_MARGIN)
    else:
        label = "중화"
        # 중화는 중심(0.40)에 가까울수록 '확실한 중화'. 경계 근접은 low.
        centeredness = min(SIN_GANG_THRESHOLD - ratio, ratio - SIN_YAK_THRESHOLD)
        confidence = _grade(centeredness, CONF_NEUTRAL_HIGH, CONF_NEUTRAL_MEDIUM)

    # 통근(通根): 일간/인성이 어느 지지의 '본기'에 뿌리내리면 True(약한 여기 뿌리 제외).
    tonggeun = any(
        gan_ohaeng(get_primary_stem(p.ji)) in ally_set
        for pos in ("year", "month", "day", "hour")
        if (p := getattr(pillars, pos, None)) is not None
    )

    # 시주 미상: 분포 정규화가 흔들려 라벨이 바뀔 수 있어 신뢰도를 한 단계 낮춘다.
    if not has_hour:
        confidence = _downgrade(confidence)

    notes: list[str] = []
    if deuk_ryeong:
        notes.append("득령(월지 본기가 아군)")
    if deuk_ji:
        notes.append("득지(일지 본기가 아군)")
    if tonggeun:
        notes.append("통근(일간/인성이 지지 본기에 뿌리)")
    if not has_hour:
        notes.append("시주 미상 — 강약 신뢰도 하향")
    notes.append("월률분야 일수 가중 계분법 적용")

    return StrengthResult(
        label=label,
        ally_ratio=round(ratio, 4),
        deuk_ryeong=deuk_ryeong,
        deuk_ji=deuk_ji,
        ally_score=round(ally_score, 4),
        hostile_score=round(total - ally_score, 4),
        total_score=round(total, 4),
        ally_elements=allies,
        notes=tuple(notes),
        confidence=confidence,
        breakdown={k.value: round(v, 4) for k, v in elem_sum.items()},
    )

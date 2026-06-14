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

from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.jijanggan import StageType, get_jijanggan, get_primary_stem
from src.engine.schema import FourPillars

StrengthLabel = Literal["신강", "신약", "중화"]

# 학술파 計分法 위치 배점 — 천간4 + 지지본기4, 합 ~120. 월지(月令)가 압도(40).
POS_WEIGHT: dict[str, float] = {
    "year_gan": 8.0, "month_gan": 12.0, "day_gan": 12.0, "hour_gan": 12.0,
    "year_ji": 4.0, "month_ji": 40.0, "day_ji": 12.0, "hour_ji": 12.0,
}
# 한 지지 내부 분할 비율(엔진 기존 1.0/0.5/0.3 재사용) — 지지 배점을 이 비율로 나눔.
STAGE_RATIO: dict[StageType, float] = {
    StageType.JEONGGI: 1.0,
    StageType.JUNGGI: 0.5,
    StageType.YEOGI: 0.3,
}
# 임계값(계분법 비율 기준): 신강 ≥0.50 / 신약 ≤0.40 / 그 사이 중화.
SIN_GANG_THRESHOLD = 0.50
SIN_YAK_THRESHOLD = 0.40
# 월지 본기가 비겁(건록·양인격)일 때만 득령 보너스.
DEUK_RYEONG_BONUS = 0.03
# 신뢰도 등급: 판정 경계로부터 거리(margin)가 멀수록 확실.
#   high=명백(경계서 멀다) / medium=보통 / low=경계 근처(유파 따라 갈릴 수 있음).
#   '정직한 불확실성 표면화' — 경계 명조는 low로 표기해 과신을 피한다.
CONF_HIGH_MARGIN = 0.08
CONF_MEDIUM_MARGIN = 0.03

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
    """사주 → 신강신약. 학술파 計分法(위치 배점)으로 일간 아군 비율을 산정.

    아군 = 비겁(同氣, 일간 오행) + 인성(生我, 부모 오행).
    각 위치에 고정 배점(POS_WEIGHT)을 두고, 지지 배점은 지장간을 STAGE_RATIO 로 분할.
    월지(月令) 본기 배점이 40으로 압도적이라 득령이 강약을 좌우한다(건록격=신강 보장).
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
        # 지지 — 배점을 지장간 STAGE_RATIO 로 분할
        bw = POS_WEIGHT[f"{pos}_ji"]
        hs = get_jijanggan(pillar.ji)
        norm = sum(STAGE_RATIO[h.stage] for h in hs)
        for h in hs:
            piece = bw * STAGE_RATIO[h.stage] / norm
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
        margin = ratio - SIN_GANG_THRESHOLD
    elif ratio <= SIN_YAK_THRESHOLD:
        label = "신약"
        margin = SIN_YAK_THRESHOLD - ratio
    else:
        label = "중화"
        # 중화대: 양 경계 중 가까운 쪽까지의 거리(경계에 가까울수록 불확실).
        margin = min(SIN_GANG_THRESHOLD - ratio, ratio - SIN_YAK_THRESHOLD)

    if margin >= CONF_HIGH_MARGIN:
        confidence = "high"
    elif margin >= CONF_MEDIUM_MARGIN:
        confidence = "medium"
    else:
        confidence = "low"

    # 통근(通根): 일간 오행/인성이 지지 지장간에 뿌리내리는가.
    tonggeun = any(
        gan_ohaeng(h.gan) in ally_set
        for pos in ("year", "month", "day", "hour")
        if (p := getattr(pillars, pos, None)) is not None
        for h in get_jijanggan(p.ji)
    )

    notes: list[str] = []
    if deuk_ryeong:
        notes.append("득령(월지 본기가 아군)")
    if deuk_ji:
        notes.append("득지(일지 본기가 아군)")
    if tonggeun:
        notes.append("통근(일간이 지지에 뿌리)")
    notes.append("학술파 계분법(월령 본기 40점) 적용")

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

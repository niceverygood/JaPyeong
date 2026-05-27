"""택일(擇日) — 사용자 사주 대비 특정 일자의 길흉 점수.

⚠ 잠정(provisional). 실제 전통 택일은 신살(천을귀인·정마성·황도흑도 등)을 두루
   본다. 본 엔진은 자평 결정론 엔진이 가진 도구(천간·지지 합/충/형, 십성, 오행)
   만 사용한다. 신살 통설표 채택 여부는 자문위원 정책 9 미확정.

스코어 (-5..+5, event_type 별 보너스 별도):
  - 일운 천간 vs 일간 십성:
      * 정인/비견 → +1
      * 식신 → +0.5
      * 정관 → +0.5 (정도)
      * 편관(칠살)/상관 → -0.5 (자극)
      * 편재/정재 → +0.3
  - 일운 지지 vs 사주 일지(natal day_ji):
      * 육합 → +1.5
      * 충 → -2
      * 같은 지지(伏吟) → -0.5
  - event_type 보너스:
      * marriage  : 일지 합 +1, 일지 충 추가 -1, 정관/정인 천간 +0.5
      * moving    : 지지 寅申巳亥(역마) → +0.5
      * business  : 천간 정재/편재 +0.5, 일지 충 추가 -0.5
      * contract  : 정인 +0.5, 정관 +0.5
      * general   : 보너스 없음
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from src.engine import sewoon
from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.schema import FourPillars, Pillar
from src.engine.ten_gods import TenGod, get_ten_god

EventType = str  # "marriage" | "moving" | "business" | "contract" | "general"

# 십성별 기본 점수 (일간 vs 일운 천간)
_TEN_GOD_BASE: dict[TenGod, float] = {
    TenGod.JEONG_IN: 1.0,
    TenGod.PYEON_IN: 0.5,
    TenGod.BI_GYEON: 1.0,
    TenGod.GYEOP_JAE: 0.3,
    TenGod.SIK_SIN: 0.5,
    TenGod.SANG_GWAN: -0.5,
    TenGod.JEONG_GWAN: 0.5,
    TenGod.PYEON_GWAN: -0.5,
    TenGod.JEONG_JAE: 0.3,
    TenGod.PYEON_JAE: 0.3,
}

_YUKHAP = {
    frozenset(p) for p in [("子", "丑"), ("寅", "亥"), ("卯", "戌"),
                          ("辰", "酉"), ("巳", "申"), ("午", "未")]
}
_CHUNG = {
    frozenset(p) for p in [("子", "午"), ("丑", "未"), ("寅", "申"),
                          ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
}
_YEOKMA = frozenset({"寅", "申", "巳", "亥"})


@dataclass(frozen=True, slots=True)
class CandidateDate:
    """택일 후보 한 건."""

    date: date
    day_pillar: Pillar
    score: float
    label: str  # 대길/길/평/주의/흉
    ten_god: str  # 일운 천간이 일간 기준 무엇인지 (한글)
    reasons: list[str]


_LABEL_THRESHOLDS = (
    (2.5, "대길"),
    (1.0, "길"),
    (-1.0, "평"),
    (-2.5, "주의"),
)


def _label_for(score: float) -> str:
    for threshold, label in _LABEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "흉"


def _ji_pair_score(
    day_ji: str, natal_day_ji: str
) -> tuple[float, list[str]]:
    if day_ji == natal_day_ji:
        return -0.5, ["일지와 같음(伏吟)"]
    pair = frozenset((day_ji, natal_day_ji))
    if pair in _CHUNG:
        return -2.0, [f"일지({natal_day_ji})와 충(沖)"]
    if pair in _YUKHAP:
        return 1.5, [f"일지({natal_day_ji})와 육합(六合)"]
    return 0.0, []


def _event_bonus(
    event_type: EventType, day_p: Pillar, natal: FourPillars, day_god: TenGod
) -> tuple[float, list[str]]:
    bonus = 0.0
    reasons: list[str] = []
    pair = frozenset((day_p.ji, natal.day.ji))

    if event_type == "marriage":
        if pair in _YUKHAP:
            bonus += 1.0
            reasons.append("결혼 보너스: 일지 합")
        if pair in _CHUNG:
            bonus -= 1.0
            reasons.append("결혼 페널티: 일지 충")
        if day_god in (TenGod.JEONG_GWAN, TenGod.JEONG_IN):
            bonus += 0.5
            reasons.append(f"결혼 보너스: 천간 {day_god.value}")
    elif event_type == "moving":
        if day_p.ji in _YEOKMA:
            bonus += 0.5
            reasons.append("이주 보너스: 일지 역마(寅申巳亥)")
    elif event_type == "business":
        if day_god in (TenGod.JEONG_JAE, TenGod.PYEON_JAE):
            bonus += 0.5
            reasons.append(f"사업 보너스: 천간 {day_god.value}")
        if pair in _CHUNG:
            bonus -= 0.5
            reasons.append("사업 페널티: 일지 충")
    elif event_type == "contract":
        if day_god in (TenGod.JEONG_IN, TenGod.JEONG_GWAN):
            bonus += 0.5
            reasons.append(f"계약 보너스: 천간 {day_god.value}")
    return bonus, reasons


def score_date(
    target: date,
    natal: FourPillars,
    event_type: EventType = "general",
) -> CandidateDate:
    """특정 날짜를 사용자 사주 대비 점수화."""
    day_p = sewoon.il_un(target)
    day_god = get_ten_god(natal.day.gan, day_p.gan)
    reasons: list[str] = []

    score = _TEN_GOD_BASE.get(day_god, 0.0)
    reasons.append(f"천간 {day_p.gan}({day_god.value}) → {_TEN_GOD_BASE.get(day_god, 0.0):+}")

    ji_score, ji_reasons = _ji_pair_score(day_p.ji, natal.day.ji)
    score += ji_score
    reasons.extend(ji_reasons)

    bonus, ev_reasons = _event_bonus(event_type, day_p, natal, day_god)
    score += bonus
    reasons.extend(ev_reasons)

    # 클램프
    score = max(-5.0, min(5.0, round(score, 2)))
    return CandidateDate(
        date=target,
        day_pillar=day_p,
        score=score,
        label=_label_for(score),
        ten_god=day_god.value,
        reasons=reasons,
    )


def select_dates(
    natal: FourPillars,
    start: date,
    end: date,
    event_type: EventType = "general",
    top_n: int = 5,
) -> list[CandidateDate]:
    """기간 내 모든 날을 점수화 후 상위 top_n 반환 (점수 내림차순, 날짜 빠른 순).

    기간 최대 365일(1년)로 제한 — 그 이상은 ValueError.
    """
    if end < start:
        raise ValueError("end 가 start 보다 앞입니다.")
    span = (end - start).days
    if span > 365:
        raise ValueError(f"기간이 너무 깁니다(최대 365일, 입력 {span}일).")

    candidates: list[CandidateDate] = []
    cur = start
    while cur <= end:
        candidates.append(score_date(cur, natal, event_type))
        cur = cur + timedelta(days=1)

    # 점수 내림차순, 동점이면 날짜 빠른 순
    candidates.sort(key=lambda c: (-c.score, c.date))
    if top_n <= 0:
        return candidates
    return candidates[:top_n]


def _suppress_unused() -> Ohaeng:  # pragma: no cover
    return gan_ohaeng("甲")

"""용신(用神) — 사주의 핵심 균형추. ⚠ 잠정(provisional).

근거(억부 통설, myeongri-policy.md 항목 8 default `EOKBU`):
  - 신강: 일간을 누르거나 빼주는 오행이 필요 → 식상(자식 오행)을 용신.
  - 신약: 일간을 돕는 오행이 필요 → 인성(부모 오행)을 용신.
  - 중화: 잠정 식상으로 두되 notes로 조후/통관 검토 필요 표기.

희신·기신·구신 도출(오행 관계 기준):
  - 희신: 용신을 生하는 오행.
  - 기신: 용신을 克하는 오행.
  - 구신: 기신을 生하는(=돕는) 오행.

⚠ 자문위원 정책 8 확정 + 검증 케이스 50건+ 전까지 모두 provisional.
조후·통관·병약 정밀 규칙은 본 구현 범위 밖.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.engine import strength as st
from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.schema import FourPillars

# 오행 상생: a 가 生하는 오행 (자식)
_SAENG_NEXT: dict[Ohaeng, Ohaeng] = {
    Ohaeng.MOK: Ohaeng.HWA,
    Ohaeng.HWA: Ohaeng.TO,
    Ohaeng.TO: Ohaeng.GEUM,
    Ohaeng.GEUM: Ohaeng.SU,
    Ohaeng.SU: Ohaeng.MOK,
}
# 오행 상극: a 가 克하는 오행
_GEUK_NEXT: dict[Ohaeng, Ohaeng] = {
    Ohaeng.MOK: Ohaeng.TO,
    Ohaeng.HWA: Ohaeng.GEUM,
    Ohaeng.TO: Ohaeng.SU,
    Ohaeng.GEUM: Ohaeng.MOK,
    Ohaeng.SU: Ohaeng.HWA,
}


def _parent_of(child: Ohaeng) -> Ohaeng:
    for parent, descendant in _SAENG_NEXT.items():
        if descendant is child:
            return parent
    raise AssertionError("오행 상생 정의 누락")  # pragma: no cover


def _controller_of(target: Ohaeng) -> Ohaeng:
    """target을 克하는 오행."""
    for controller, victim in _GEUK_NEXT.items():
        if victim is target:
            return controller
    raise AssertionError("오행 상극 정의 누락")  # pragma: no cover


@dataclass(frozen=True, slots=True)
class YongsinResult:
    """용신·희신·기신·구신."""

    yongsin: Ohaeng
    huishin: Ohaeng
    gisin: Ohaeng
    gushin: Ohaeng
    method: str  # "eokbu" | "johu" | "hybrid"
    based_on_strength: str  # "신강" | "신약" | "중화"
    notes: tuple[str, ...] = ()
    confidence: str = "provisional"


def derive_yongsin(pillars: FourPillars) -> YongsinResult:
    """억부(EOKBU) 잠정 용신 도출."""
    s = st.assess_strength(pillars)
    dm_oh = gan_ohaeng(pillars.day.gan)

    if s.label == "신약":
        yongsin = _parent_of(dm_oh)  # 인성
        notes: tuple[str, ...] = ("신약 — 인성을 용신으로(잠정)",)
    elif s.label == "신강":
        yongsin = _SAENG_NEXT[dm_oh]  # 식상
        notes = ("신강 — 식상을 용신으로(잠정)",)
    else:
        yongsin = _SAENG_NEXT[dm_oh]
        notes = (
            "중화 — 잠정 식상 용신 placeholder. 조후/통관 정밀 검토는 자문위원 확정 후.",
        )

    huishin = _parent_of(yongsin)         # 용신을 生
    gisin = _controller_of(yongsin)       # 용신을 克
    gushin = _parent_of(gisin)            # 기신을 生(돕는)

    return YongsinResult(
        yongsin=yongsin,
        huishin=huishin,
        gisin=gisin,
        gushin=gushin,
        method="eokbu",
        based_on_strength=s.label,
        notes=notes,
    )

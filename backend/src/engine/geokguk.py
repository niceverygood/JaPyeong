"""격국(格局) — 사주의 구조 패턴 판별. ⚠ 잠정(provisional).

근거(자평진전 통설, myeongri-policy.md 항목 7 default `TUCHUL_FIRST`):
  1. 월지(月支) 지장간 정기·중기·여기 순으로 천간 자리(년·월·시간)에 투출(透出) 검사.
  2. 첫 투출 천간의 십성을 격(格) 이름으로 채택.
  3. 어느 것도 투출 안 됐으면 정기의 십성을 본기(本氣)로 채택.
  4. 일간(day_gan)은 자기 자신이므로 투출 검사에서 제외.

이 단순 구현은 잡기격·외격·합거 등 정밀 규칙을 다루지 않는다. 자문위원 정책 7
확정 후 정밀 구현으로 교체. 모든 결과는 confidence="provisional".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.engine.jijanggan import StageType, get_jijanggan
from src.engine.schema import FourPillars
from src.engine.ten_gods import TenGod, get_ten_god

# 10종 격국명 (정통 8격 + 비견격·겁재격)
_TEN_GOD_TO_GEOKGUK: dict[TenGod, str] = {
    TenGod.BI_GYEON: "비견격",
    TenGod.GYEOP_JAE: "겁재격",
    TenGod.SIK_SIN: "식신격",
    TenGod.SANG_GWAN: "상관격",
    TenGod.JEONG_JAE: "정재격",
    TenGod.PYEON_JAE: "편재격",
    TenGod.JEONG_GWAN: "정관격",
    TenGod.PYEON_GWAN: "편관격",
    TenGod.JEONG_IN: "정인격",
    TenGod.PYEON_IN: "편인격",
}

GEOKGUK_NAMES = frozenset(_TEN_GOD_TO_GEOKGUK.values())

# 천간 투출 검사 대상 위치 (일간 제외)
_TUCHUL_POSITIONS = ("year_gan", "month_gan", "hour_gan")


@dataclass(frozen=True, slots=True)
class GeokgukResult:
    """격국 판별 결과."""

    name: str  # "정관격" 등
    ten_god: TenGod
    based_on: Literal["transparent", "primary"]  # 투출 매치 / 본기 fallback
    based_gan: str  # 격을 만든 천간 (한자)
    based_stage: str  # 정기/중기/여기 (transparent일 때만 의미)
    transparent_position: str | None  # year_gan/month_gan/hour_gan or None
    confidence: str = "provisional"


def _other_gans(pillars: FourPillars) -> dict[str, str]:
    """일간 제외 천간 위치 → 천간 글자."""
    out: dict[str, str] = {}
    for pos, attr in (("year_gan", "year"), ("month_gan", "month"), ("hour_gan", "hour")):
        pillar = getattr(pillars, attr, None)
        if pillar is not None:
            out[pos] = pillar.gan
    return out


def determine_geokguk(pillars: FourPillars) -> GeokgukResult:
    """월지 지장간 투출 우선(TUCHUL_FIRST) — 통설 단순 구현."""
    dm = pillars.day.gan
    month_ji = pillars.month.ji
    hiddens = get_jijanggan(month_ji)  # [餘氣, (中氣), 正氣]
    # 정기 → 중기 → 여기 순으로 투출 검사
    stage_order = {StageType.JEONGGI: 0, StageType.JUNGGI: 1, StageType.YEOGI: 2}
    ordered = sorted(hiddens, key=lambda h: stage_order[h.stage])
    other_gans = _other_gans(pillars)

    for h in ordered:
        # 일간과 같은 글자는 "자기 자신" — 투출 검사에서 제외해 격에 채택 금지
        if h.gan == dm:
            continue
        for pos in _TUCHUL_POSITIONS:
            if other_gans.get(pos) == h.gan:
                tg = get_ten_god(dm, h.gan)
                return GeokgukResult(
                    name=_TEN_GOD_TO_GEOKGUK[tg],
                    ten_god=tg,
                    based_on="transparent",
                    based_gan=h.gan,
                    based_stage=h.stage.value,
                    transparent_position=pos,
                )

    # 투출 없음 → 정기 본기로 fallback (일간 자신이면 그래도 채택 = 비견격)
    primary = next(h for h in hiddens if h.stage == StageType.JEONGGI)
    tg = get_ten_god(dm, primary.gan)
    return GeokgukResult(
        name=_TEN_GOD_TO_GEOKGUK[tg],
        ten_god=tg,
        based_on="primary",
        based_gan=primary.gan,
        based_stage=primary.stage.value,
        transparent_position=None,
    )

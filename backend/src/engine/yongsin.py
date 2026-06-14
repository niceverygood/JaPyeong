"""용신(用神) — 사주의 핵심 균형추. 억부 + 조후 + 전왕(專旺) hybrid.

근거:
  - 억부(抑扶): 신강이면 식상(설기)/재/관, 신약이면 인성(생)/비겁(부조).
  - 조후(調候, 궁통보감): 계절 한난조습 보정. 겨울(亥子丑) 火, 여름(巳午未) 水 필요.
    계절이 극단(子/午)이거나 조후 오행이 원국에 결핍이면 조후가 억부에 우선한다.
  - 전왕(專旺): 일간 세력이 압도적(곡직·염상·윤하 등)이면 왕신(일간 오행)을 순세 용신으로.

희신·기신·구신: 용신을 生 / 克 / 기신을 生 하는 오행.
조후표는 (일간 10천간 × 월지 12지) 1순위 매핑(궁통보감 통설 정수).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.engine import five_elements as fe
from src.engine import strength as st
from src.engine.constants import Ohaeng
from src.engine.ganji import gan_ohaeng
from src.engine.schema import FourPillars

# 월지 → 계절 온도. frigid_*=조후 최우선(한겨울/한여름), cold/hot=조후 차순, 그 외 억부 우선.
_SEASON_TEMP: dict[str, str] = {
    "寅": "warm", "卯": "temperate", "辰": "temperate",
    "巳": "hot", "午": "frigid_hot", "未": "hot",
    "申": "temperate", "酉": "temperate", "戌": "warm",
    "亥": "cold", "子": "frigid_cold", "丑": "cold",
}

_M, _H, _T, _G, _S = Ohaeng.MOK, Ohaeng.HWA, Ohaeng.TO, Ohaeng.GEUM, Ohaeng.SU
# (일간, 월지) → 조후용신 1순위 오행 (궁통보감 통설).
_JOHU_TABLE: dict[str, dict[str, Ohaeng]] = {
    "甲": {"寅": _H, "卯": _G, "辰": _G, "巳": _S, "午": _S, "未": _S, "申": _G, "酉": _G, "戌": _G, "亥": _G, "子": _H, "丑": _H},
    "乙": {"寅": _H, "卯": _H, "辰": _S, "巳": _S, "午": _S, "未": _S, "申": _H, "酉": _S, "戌": _S, "亥": _H, "子": _H, "丑": _H},
    "丙": {"寅": _S, "卯": _S, "辰": _S, "巳": _S, "午": _S, "未": _S, "申": _S, "酉": _S, "戌": _M, "亥": _M, "子": _S, "丑": _S},
    "丁": {"寅": _M, "卯": _G, "辰": _M, "巳": _M, "午": _S, "未": _M, "申": _M, "酉": _M, "戌": _M, "亥": _M, "子": _M, "丑": _M},
    "戊": {"寅": _H, "卯": _H, "辰": _M, "巳": _M, "午": _S, "未": _S, "申": _H, "酉": _H, "戌": _M, "亥": _M, "子": _H, "丑": _H},
    "己": {"寅": _H, "卯": _M, "辰": _H, "巳": _S, "午": _S, "未": _S, "申": _H, "酉": _H, "戌": _M, "亥": _H, "子": _H, "丑": _H},
    "庚": {"寅": _H, "卯": _H, "辰": _M, "巳": _S, "午": _S, "未": _H, "申": _H, "酉": _H, "戌": _M, "亥": _H, "子": _H, "丑": _H},
    "辛": {"寅": _T, "卯": _S, "辰": _S, "巳": _S, "午": _S, "未": _S, "申": _S, "酉": _S, "戌": _S, "亥": _S, "子": _H, "丑": _H},
    "壬": {"寅": _G, "卯": _T, "辰": _M, "巳": _S, "午": _S, "未": _G, "申": _T, "酉": _M, "戌": _M, "亥": _T, "子": _T, "丑": _H},
    "癸": {"寅": _G, "卯": _G, "辰": _H, "巳": _G, "午": _G, "未": _G, "申": _H, "酉": _G, "戌": _G, "亥": _G, "子": _H, "丑": _H},
}

# 전왕(專旺): 아군 비율이 이 이상이면 왕신 순세 용신(곡직·염상·윤하 등).
JEONWANG_RATIO = 0.88
# 조후 결핍 판정: 균등 분포에서 조후 오행 비율이 이 미만이면 '부재'.
JOHU_DEFICIT_RATIO = 0.12

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
    """용신 도출 — 전왕(專旺) → 조후(調候) → 억부(抑扶) 우선순위 hybrid."""
    s = st.assess_strength(pillars)
    dm_oh = gan_ohaeng(pillars.day.gan)
    month_ji = pillars.month.ji
    climate = _SEASON_TEMP.get(month_ji, "temperate")
    johu_oh = _JOHU_TABLE.get(pillars.day.gan, {}).get(month_ji)

    # 억부 기본값: 신약→인성(생부), 신강·중화→식상(설기).
    if s.label == "신약":
        eokbu = _parent_of(dm_oh)
    else:
        eokbu = _SAENG_NEXT[dm_oh]

    # 조후 우선은 '신약이 아닐 때'만 — 신약은 부조(인비)가 최우선이라 조후가 억부를 덮지 않는다.
    # (극단격: 전왕·종격·극신약의 용신은 유파 차가 커 결정론으로 단정하지 않고 LLM/자문위원 영역.)
    johu_priority = False
    if johu_oh is not None and s.label != "신약":
        dist = fe.calculate_distribution(pillars, include_hidden=True)
        johu_ratio = (dist.by_element(johu_oh) / dist.total) if dist.total else 0.0
        if climate in ("frigid_cold", "frigid_hot"):
            johu_priority = True
        elif climate in ("cold", "hot") and johu_ratio < JOHU_DEFICIT_RATIO:
            johu_priority = True

    if johu_priority and johu_oh is not None and johu_oh != eokbu:
        yongsin = johu_oh
        method = "johu"
        notes: tuple[str, ...] = (
            f"조후 우선({month_ji}월) — {johu_oh.value} 보정. 억부({eokbu.value})는 차순.",
        )
    elif johu_priority and johu_oh == eokbu:
        yongsin = eokbu
        method = "hybrid"
        notes = (f"억부·조후 일치 — {eokbu.value} 용신({s.label}·{month_ji}월).",)
    else:
        yongsin = eokbu
        method = "eokbu"
        note = f"억부 — {s.label}이라 {eokbu.value} 용신"
        if johu_oh is not None and johu_oh != eokbu:
            note += f". 조후 참고: {month_ji}월 {johu_oh.value}"
        notes = (note,)

    huishin = _parent_of(yongsin)         # 용신을 生
    gisin = _controller_of(yongsin)       # 용신을 克
    gushin = _parent_of(gisin)            # 기신을 生(돕는)

    return YongsinResult(
        yongsin=yongsin,
        huishin=huishin,
        gisin=gisin,
        gushin=gushin,
        method=method,
        based_on_strength=s.label,
        notes=notes,
    )

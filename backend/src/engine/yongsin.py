"""용신(用神) — 사주의 핵심 균형추. 억부(抑扶) + 조후(調候) hybrid.

근거:
  - 억부(抑扶): 신약이면 인성(생부), 신강·중화면 식상(설기)을 기본 용신으로.
  - 조후(調候, 궁통보감): 계절 한난조습 보정. 한겨울/한여름이면서 보정 오행이
    원국에 결핍일 때만 조후가 억부에 우선한다(이미 충분하면 억부로 회귀).
    조후표는 '순수 한난조습 1순위 단일 오행'을 담는다 — 격국·벽갑(劈甲)용신이 아니라
    겨울→火(온난)/여름→水(윤습) 같은 한난 보정 오행이다.

희신·기신·구신: 용신을 生 / 克 / 기신을 生 하는 오행.

⚠ 극단격(전왕·종격·극신약)의 용신은 유파 차가 커 결정론으로 단정하지 않고
   LLM 교차검증·자문위원 영역으로 유보한다(본 모듈은 억부·조후만 단정).
조후표 출처: 궁통보감(窮通寶鑑) 통설을 블라인드 앙상블 3인 재구성 + 한난조습
   1순위 적대적 판정으로 교정한 값.
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
# (일간, 월지) → 순수 한난조습(調候) 1순위 보정 오행.
# 궁통보감 통설을 블라인드 앙상블 3인 + 한난조습 적대적 판정으로 교정(2026-06).
# 원칙: 한겨울(亥子丑)=火 온난(火일간 丙丁은 木으로 火 부조), 한여름(巳午未)=水 윤습,
#       가을 조토(戌)=水 윤택, 금왕추월(申酉)의 木일간=火 제금. '벽갑·격국용신'은 배제.
_JOHU_TABLE: dict[str, dict[str, Ohaeng]] = {
    "甲": {"寅": _H, "卯": _H, "辰": _G, "巳": _S, "午": _S, "未": _S, "申": _H, "酉": _H, "戌": _S, "亥": _H, "子": _H, "丑": _H},
    "乙": {"寅": _H, "卯": _H, "辰": _S, "巳": _S, "午": _S, "未": _S, "申": _H, "酉": _H, "戌": _S, "亥": _H, "子": _H, "丑": _H},
    "丙": {"寅": _S, "卯": _S, "辰": _S, "巳": _S, "午": _S, "未": _S, "申": _S, "酉": _S, "戌": _M, "亥": _M, "子": _M, "丑": _S},
    "丁": {"寅": _M, "卯": _G, "辰": _M, "巳": _S, "午": _S, "未": _S, "申": _M, "酉": _M, "戌": _M, "亥": _M, "子": _M, "丑": _M},
    "戊": {"寅": _H, "卯": _H, "辰": _S, "巳": _S, "午": _S, "未": _S, "申": _H, "酉": _H, "戌": _S, "亥": _H, "子": _H, "丑": _H},
    "己": {"寅": _H, "卯": _H, "辰": _S, "巳": _S, "午": _S, "未": _S, "申": _H, "酉": _H, "戌": _S, "亥": _H, "子": _H, "丑": _H},
    "庚": {"寅": _H, "卯": _H, "辰": _M, "巳": _S, "午": _S, "未": _S, "申": _H, "酉": _H, "戌": _M, "亥": _H, "子": _H, "丑": _H},
    "辛": {"寅": _S, "卯": _S, "辰": _S, "巳": _S, "午": _S, "未": _S, "申": _S, "酉": _S, "戌": _S, "亥": _H, "子": _H, "丑": _H},
    "壬": {"寅": _H, "卯": _T, "辰": _M, "巳": _S, "午": _S, "未": _G, "申": _H, "酉": _M, "戌": _H, "亥": _H, "子": _H, "丑": _H},
    "癸": {"寅": _H, "卯": _G, "辰": _H, "巳": _G, "午": _G, "未": _G, "申": _H, "酉": _H, "戌": _G, "亥": _H, "子": _H, "丑": _H},
}

# 조후 결핍 판정: 보정 오행 비율이 이 미만이면 '부재'(억부 대신 조후 우선).
JOHU_DEFICIT_RATIO = 0.12
# 한겨울/한여름(子·午)은 조후를 더 강하게 요하나, 보정 오행이 이미 이 이상으로
# 풍부하면 조후는 충족된 것으로 보고 억부로 회귀한다(과도한 조후 강제 방지).
FRIGID_SUFFICIENT_RATIO = 0.30

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
    """용신 도출 — 조후(調候) → 억부(抑扶) 우선순위 hybrid.

    극단격(전왕·종·극신약)은 단정하지 않고 억부·조후 경로로만 방향을 제시한다.
    """
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
            # 한겨울/한여름: 보정 오행이 이미 풍부(>=0.30)하면 조후 충족 → 억부 회귀.
            johu_priority = johu_ratio < FRIGID_SUFFICIENT_RATIO
        elif climate in ("cold", "hot"):
            johu_priority = johu_ratio < JOHU_DEFICIT_RATIO

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

    # 중화 명조의 용신은 병약·통관 등 개별 판단 영역 — 단정 대신 방향 참고로 표기.
    if s.label == "중화":
        notes = notes + ("중화 명조 — 용신은 병약·통관 등 개별판단 영역이라 방향 참고용.",)

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

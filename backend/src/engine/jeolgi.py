"""24절기(節氣) — 월주 경계·세수 산출.

근거: 자평명리는 월주를 12절(節)로 정한다(WoljuBoundaryPolicy.JEOL).
세수는 입춘 기준(SesuPolicy.IPCHUN).

절입 시각은 sxtwl(`getJieQiByYear`)로 산출한다. sxtwl의 jieqi 시각은
베이징(UTC+8) 벽시계 기준 율리우스일이므로, UTC로 환산한 뒤 zoneinfo로
대상 timezone(default Asia/Seoul)의 KST(naive)로 변환한다(한국 표준시 역사 자동 반영).
  검증: 立春 2024 = 2024-02-04 17:26:53 KST (test_jeolgi).
  TODO(policy): 라이브러리 채택은 myeongri-policy.md 항목 12 — 자문위원 확정 필요.

24절기 중 12절(節, 월의 시작)과 월지:
  입춘→寅 경칩→卯 청명→辰 입하→巳 망종→午 소서→未
  입추→申 백로→酉 한로→戌 입동→亥 대설→子 소한→丑

순수 결정론적: 같은 입력 → 항상 같은 출력.
"""

import bisect
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import sxtwl

from src.engine.policy import (
    MyeongriPolicy,
    SesuPolicy,
    WoljuBoundaryPolicy,
    get_default_policy,
)

# sxtwl jieqi 인덱스(0=동지 … 23=대설) → 24절기 한자명
_JQ_NAME = (
    "冬至", "小寒", "大寒", "立春", "雨水", "驚蟄", "春分", "清明",
    "穀雨", "立夏", "小滿", "芒種", "夏至", "小暑", "大暑", "立秋",
    "處暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
)

# 12절(節, 홀수 인덱스) → 월지. 절기 jieqi 인덱스 기준.
_NODE_BRANCH: dict[int, str] = {
    3: "寅",   # 입춘
    5: "卯",   # 경칩
    7: "辰",   # 청명
    9: "巳",   # 입하
    11: "午",  # 망종
    13: "未",  # 소서
    15: "申",  # 입추
    17: "酉",  # 백로
    19: "戌",  # 한로
    21: "亥",  # 입동
    23: "子",  # 대설
    1: "丑",   # 소한
}

# sxtwl 절기 시각 기준 = 중국 표준시(UTC+8, 근대 안정). _jd_to_local에서 환산.
_DEFAULT_TZ = "Asia/Seoul"


@dataclass(frozen=True, slots=True)
class JeolgiPoint:
    """절기 1개."""

    name: str  # 한자명
    index: int  # sxtwl jieqi 인덱스 0~23
    instant: datetime  # 절입 시각 (대상 timezone, naive)
    is_jeol: bool  # 12절(월 시작)이면 True
    month_branch: str | None  # 절일 때 월지, 아니면 None


def _jd_to_local(jd: float, tz: str) -> datetime:
    """sxtwl 절기 jd(베이징 벽시계 기준) → 대상 timezone naive datetime."""
    beijing_wall = datetime(1970, 1, 1) + timedelta(seconds=(jd - 2440587.5) * 86400.0)
    utc = (beijing_wall - timedelta(hours=8)).replace(tzinfo=UTC)
    return utc.astimezone(ZoneInfo(tz)).replace(tzinfo=None)


def solar_terms(year: int, tz: str = _DEFAULT_TZ) -> list[JeolgiPoint]:
    """입춘(year)부터 입춘(year+1)까지 25개 절기를 시간순으로 반환."""
    points: list[JeolgiPoint] = []
    for info in sxtwl.getJieQiByYear(year):
        idx = info.jqIndex
        is_jeol = idx in _NODE_BRANCH
        points.append(
            JeolgiPoint(
                name=_JQ_NAME[idx],
                index=idx,
                instant=_jd_to_local(info.jd, tz),
                is_jeol=is_jeol,
                month_branch=_NODE_BRANCH.get(idx),
            )
        )
    points.sort(key=lambda p: p.instant)
    return points


def jeol_boundaries(year: int, tz: str = _DEFAULT_TZ) -> list[JeolgiPoint]:
    """해당 세수 연도의 12절(입춘~소한)을 시간순으로 반환.

    sxtwl getJieQiByYear(year)는 입춘(year)~입춘(year+1)을 주므로,
    마지막 입춘(year+1)을 제외한 12절을 취한다.
    """
    jeols = [p for p in solar_terms(year, tz) if p.is_jeol]
    # 입춘이 처음과 끝(다음 해)에 모두 포함 → 마지막 입춘 제거
    return jeols[:12]


def _node_timeline(dt: datetime, tz: str) -> list[tuple[datetime, str]]:
    """dt를 포함하는 구간 판정을 위한 (절입시각, 월지) 정렬 목록."""
    seen: dict[datetime, str] = {}
    for y in (dt.year - 1, dt.year):
        for p in solar_terms(y, tz):
            if p.is_jeol and p.month_branch is not None:
                seen[p.instant] = p.month_branch
    return sorted(seen.items())


def month_branch_for(
    dt: datetime, policy: MyeongriPolicy | None = None, tz: str = _DEFAULT_TZ
) -> str:
    """주어진 시각이 속한 월의 지지(월지)를 반환.

    dt는 월주 판정에 사용할 시각(일반적으로 진태양시 보정 후). 미래 절입 이전,
    즉 dt 이하의 가장 최근 절(節)이 그 달을 정한다.
    """
    pol = policy or get_default_policy()
    if pol.wolju_boundary != WoljuBoundaryPolicy.JEOL:
        raise NotImplementedError(
            f"월주 경계 정책 미지원: {pol.wolju_boundary} (현재 JEOL만 구현)"
        )

    timeline = _node_timeline(dt, tz)
    instants = [t for t, _ in timeline]
    pos = bisect.bisect_right(instants, dt)
    if pos == 0:  # pragma: no cover (전년 절까지 포함하므로 도달 불가)
        raise ValueError(f"월지 판정 불가(절기 범위 밖): {dt}")
    return timeline[pos - 1][1]


def solar_year(
    dt: datetime, policy: MyeongriPolicy | None = None, tz: str = _DEFAULT_TZ
) -> int:
    """명리 연도(년주 산정용). 입춘 기준(IPCHUN).

    입춘(dt.year) 이후면 dt.year, 이전이면 dt.year - 1.
    """
    pol = policy or get_default_policy()
    if pol.sesu != SesuPolicy.IPCHUN:
        raise NotImplementedError(
            f"세수 정책 미지원: {pol.sesu} (현재 IPCHUN만 구현)"
        )

    ipchun = jeol_boundaries(dt.year, tz)[0].instant
    return dt.year if dt >= ipchun else dt.year - 1

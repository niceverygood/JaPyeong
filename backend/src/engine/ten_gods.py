"""십성(十星) — 일간(日干) 대비 다른 천간의 관계.

근거: 명리 공통. 오행 생극(生剋)으로 5개 군(비겁·식상·재성·관성·인성)을 정하고,
음양 동이(同異)로 정(正)·편(偏)을 나눠 10가지를 산출한다. 정책 의존 없음.

  - 같은 오행      : 음양 같음 → 비견, 다름 → 겁재
  - 일간이 生하는 것: 음양 같음 → 식신, 다름 → 상관
  - 일간이 剋하는 것: 음양 같음 → 편재, 다름 → 정재
  - 일간을 剋하는 것: 음양 같음 → 편관, 다름 → 정관
  - 일간을 生하는 것: 음양 같음 → 편인, 다름 → 정인

순수 결정론적. 같은 입력 → 항상 같은 출력.
"""

from collections import Counter
from enum import StrEnum

from src.engine.constants import Ohaeng
from src.engine.ganji import gan_eumyang, gan_ohaeng
from src.engine.jijanggan import get_primary_stem
from src.engine.schema import FourPillars, TenGodsCount


class TenGod(StrEnum):
    """십성. 멤버명은 romanization(코드용), 값은 한글(사용자 노출용)."""

    BI_GYEON = "비견"  # 比肩
    GYEOP_JAE = "겁재"  # 劫財
    SIK_SIN = "식신"  # 食神
    SANG_GWAN = "상관"  # 傷官
    JEONG_JAE = "정재"  # 正財
    PYEON_JAE = "편재"  # 偏財
    JEONG_GWAN = "정관"  # 正官
    PYEON_GWAN = "편관"  # 偏官
    JEONG_IN = "정인"  # 正印
    PYEON_IN = "편인"  # 偏印


# 한자 병기 (자문 답변·UI용)
TEN_GOD_HANJA: dict[TenGod, str] = {
    TenGod.BI_GYEON: "比肩",
    TenGod.GYEOP_JAE: "劫財",
    TenGod.SIK_SIN: "食神",
    TenGod.SANG_GWAN: "傷官",
    TenGod.JEONG_JAE: "正財",
    TenGod.PYEON_JAE: "偏財",
    TenGod.JEONG_GWAN: "正官",
    TenGod.PYEON_GWAN: "偏官",
    TenGod.JEONG_IN: "正印",
    TenGod.PYEON_IN: "偏印",
}

# 오행 상생 다음(生): a 가 生하는 오행
_SAENG_NEXT: dict[Ohaeng, Ohaeng] = {
    Ohaeng.MOK: Ohaeng.HWA,
    Ohaeng.HWA: Ohaeng.TO,
    Ohaeng.TO: Ohaeng.GEUM,
    Ohaeng.GEUM: Ohaeng.SU,
    Ohaeng.SU: Ohaeng.MOK,
}

# 오행 상극(剋): a 가 剋하는 오행
_GEUK_NEXT: dict[Ohaeng, Ohaeng] = {
    Ohaeng.MOK: Ohaeng.TO,
    Ohaeng.HWA: Ohaeng.GEUM,
    Ohaeng.TO: Ohaeng.SU,
    Ohaeng.GEUM: Ohaeng.MOK,
    Ohaeng.SU: Ohaeng.HWA,
}

# (오행관계, 음양동일여부) → 십성
#   오행관계: "same" | "i_produce" | "i_control" | "controls_me" | "produces_me"
_RULES: dict[tuple[str, bool], TenGod] = {
    ("same", True): TenGod.BI_GYEON,
    ("same", False): TenGod.GYEOP_JAE,
    ("i_produce", True): TenGod.SIK_SIN,
    ("i_produce", False): TenGod.SANG_GWAN,
    ("i_control", True): TenGod.PYEON_JAE,
    ("i_control", False): TenGod.JEONG_JAE,
    ("controls_me", True): TenGod.PYEON_GWAN,
    ("controls_me", False): TenGod.JEONG_GWAN,
    ("produces_me", True): TenGod.PYEON_IN,
    ("produces_me", False): TenGod.JEONG_IN,
}


def _relation(dm_oh: Ohaeng, other_oh: Ohaeng) -> str:
    if other_oh == dm_oh:
        return "same"
    if _SAENG_NEXT[dm_oh] == other_oh:
        return "i_produce"
    if _GEUK_NEXT[dm_oh] == other_oh:
        return "i_control"
    if _GEUK_NEXT[other_oh] == dm_oh:
        return "controls_me"
    if _SAENG_NEXT[other_oh] == dm_oh:
        return "produces_me"
    raise AssertionError("오행 관계 누락")  # pragma: no cover (5관계 망라)


def get_ten_god(day_master: str, other: str) -> TenGod:
    """일간(day_master) 기준 다른 천간(other)의 십성.

    천간이 아니면 ValueError (gan_ohaeng/gan_eumyang에서 발생).
    """
    dm_oh = gan_ohaeng(day_master)
    other_oh = gan_ohaeng(other)
    same_eum = gan_eumyang(day_master) == gan_eumyang(other)
    return _RULES[(_relation(dm_oh, other_oh), same_eum)]


def count_ten_gods_in_pillars(
    day_master: str,
    pillars: FourPillars,
    include_hidden: bool = False,
) -> TenGodsCount:
    """사주 기둥들의 십성 분포를 집계.

    - 천간: 년·월·시주 천간을 집계(일주 천간 = 일간 자신이므로 제외).
    - include_hidden=True: 각 지지의 正氣(본기) 천간을 추가 집계(년·월·일·시 모두).
      (지장간 中氣·餘氣는 집계 제외 — 본기만.)

    천간이 아니면 ValueError.
    """
    _ = gan_ohaeng(day_master)  # 일간 유효성 조기 검증
    counts: Counter[TenGod] = Counter()

    stems = [pillars.year.gan, pillars.month.gan]
    if pillars.hour is not None:
        stems.append(pillars.hour.gan)
    for stem in stems:
        counts[get_ten_god(day_master, stem)] += 1

    if include_hidden:
        branches = [pillars.year.ji, pillars.month.ji, pillars.day.ji]
        if pillars.hour is not None:
            branches.append(pillars.hour.ji)
        for ji in branches:
            counts[get_ten_god(day_master, get_primary_stem(ji))] += 1

    return TenGodsCount(**{god.name.lower(): n for god, n in counts.items()})

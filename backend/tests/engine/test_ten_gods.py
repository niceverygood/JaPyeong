"""십성(十星) 모듈 검증 테스트 (TDD — 구현 전 작성).

근거: 일간 대비 오행 생극(生剋) + 음양 동이(同異)로 십성을 정한다.
정책 의존 없음(명리 공통). 결정론적.

규칙:
- 같은 오행: 음양 같으면 비견, 다르면 겁재
- 일간이 生하는 오행(식상): 음양 같으면 식신, 다르면 상관
- 일간이 剋하는 오행(재성): 음양 같으면 편재, 다르면 정재
- 일간을 剋하는 오행(관성): 음양 같으면 편관, 다르면 정관
- 일간을 生하는 오행(인성): 음양 같으면 편인, 다르면 정인
"""

import pytest

from src.engine import ten_gods as tg
from src.engine.constants import CHUN_GAN
from src.engine.schema import FourPillars, Pillar, TenGodsCount

TG = tg.TenGod


# ── 비견: 같은 천간(=같은 오행·같은 음양) 10개 ──────────────────
@pytest.mark.parametrize("gan", CHUN_GAN)
def test_same_stem_is_bi_gyeon(gan):
    assert tg.get_ten_god(gan, gan) == TG.BI_GYEON


# ── 겁재: 같은 오행 다른 음양 5쌍 ─────────────────────────────
@pytest.mark.parametrize(
    "dm,other", [("甲", "乙"), ("丙", "丁"), ("戊", "己"), ("庚", "辛"), ("壬", "癸")]
)
def test_same_element_diff_eumyang_is_gyeop_jae(dm, other):
    assert tg.get_ten_god(dm, other) == TG.GYEOP_JAE
    assert tg.get_ten_god(other, dm) == TG.GYEOP_JAE  # 역도 겁재


# ── 식신/상관: 일간이 生하는 오행 10개 ───────────────────────
@pytest.mark.parametrize(
    "dm,other",  # 음양 같음 → 식신
    [("甲", "丙"), ("乙", "丁"), ("丙", "戊"), ("丁", "己"), ("戊", "庚")],
)
def test_produces_same_eumyang_is_sik_sin(dm, other):
    assert tg.get_ten_god(dm, other) == TG.SIK_SIN


@pytest.mark.parametrize(
    "dm,other",  # 음양 다름 → 상관
    [("甲", "丁"), ("乙", "丙"), ("丙", "己"), ("丁", "戊"), ("戊", "辛")],
)
def test_produces_diff_eumyang_is_sang_gwan(dm, other):
    assert tg.get_ten_god(dm, other) == TG.SANG_GWAN


# ── 정관/편관: 일간을 剋하는 오행 10개 ───────────────────────
@pytest.mark.parametrize(
    "dm,other",  # 음양 같음 → 편관
    [("甲", "庚"), ("乙", "辛"), ("丙", "壬"), ("丁", "癸"), ("戊", "甲")],
)
def test_controlled_same_eumyang_is_pyeon_gwan(dm, other):
    assert tg.get_ten_god(dm, other) == TG.PYEON_GWAN


@pytest.mark.parametrize(
    "dm,other",  # 음양 다름 → 정관
    [("甲", "辛"), ("乙", "庚"), ("丙", "癸"), ("丁", "壬"), ("戊", "乙")],
)
def test_controlled_diff_eumyang_is_jeong_gwan(dm, other):
    assert tg.get_ten_god(dm, other) == TG.JEONG_GWAN


# ── 재성/인성 보강 (편재/정재/편인/정인) ─────────────────────
@pytest.mark.parametrize(
    "dm,other,expected",
    [
        ("丙", "庚", TG.PYEON_JAE),  # 火克金 same → 편재
        ("丙", "辛", TG.JEONG_JAE),  # 火克金 diff → 정재
        ("丙", "甲", TG.PYEON_IN),  # 木生火 same → 편인
        ("丙", "乙", TG.JEONG_IN),  # 木生火 diff → 정인
    ],
)
def test_jae_in_groups(dm, other, expected):
    assert tg.get_ten_god(dm, other) == expected


def test_invalid_input_raises():
    with pytest.raises(ValueError):
        tg.get_ten_god("子", "甲")  # 지지를 일간으로
    with pytest.raises(ValueError):
        tg.get_ten_god("甲", "X")


# ── count_ten_gods_in_pillars 통합 ───────────────────────────
def _p(gan: str, ji: str) -> Pillar:
    return Pillar(gan=gan, ji=ji)


def test_count_天간_only_excludes_day_master():
    # 일간 甲. 일주 천간(甲)은 비견으로 세지 않아야 한다.
    pillars = FourPillars(
        year=_p("丙", "寅"), month=_p("丁", "卯"), day=_p("甲", "子"), hour=None
    )
    c = tg.count_ten_gods_in_pillars("甲", pillars, include_hidden=False)
    # 丙(木生火 same→식신), 丁(diff→상관). 日干 甲 제외.
    assert c == TenGodsCount(sik_sin=1, sang_gwan=1)
    assert c.bi_gyeon == 0


def test_count_with_hour_none():
    pillars = FourPillars(
        year=_p("乙", "丑"), month=_p("己", "卯"), day=_p("庚", "午"), hour=None
    )
    c = tg.count_ten_gods_in_pillars("庚", pillars, include_hidden=False)
    # 乙(金克木 diff→정재), 己(土生金 diff→정인)
    assert c == TenGodsCount(jeong_jae=1, jeong_in=1)


def test_count_include_hidden_adds_jeonggi():
    pillars = FourPillars(
        year=_p("甲", "子"), month=_p("戊", "辰"), day=_p("丙", "戌"), hour=_p("庚", "寅")
    )
    dm = "丙"
    no_hidden = tg.count_ten_gods_in_pillars(dm, pillars, include_hidden=False)
    # 천간만(일간 丙 제외): 甲→편인, 戊→식신, 庚→편재
    assert no_hidden == TenGodsCount(pyeon_in=1, sik_sin=1, pyeon_jae=1)

    with_hidden = tg.count_ten_gods_in_pillars(dm, pillars, include_hidden=True)
    # 지지 正氣 추가: 子→癸(정관), 辰→戊(식신), 戌→戊(식신), 寅→甲(편인)
    assert with_hidden == TenGodsCount(
        pyeon_in=2, sik_sin=3, pyeon_jae=1, jeong_gwan=1
    )

    # include_hidden=True 총합이 False보다 크다(지지 4개 추가).
    assert _total(with_hidden) == _total(no_hidden) + 4


def _total(c: TenGodsCount) -> int:
    return sum(getattr(c, f) for f in TenGodsCount.model_fields)

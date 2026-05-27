"""engine.compatibility 단위 테스트.

결정론적 보장:
- cross_relations 는 두 사주 사이만 검출 (각자 내부 제외)
- day_master_pair 의 십성 관계가 양방향 정확
- element_dynamic 5종(비화/A생B/B생A/A극B/B극A) 정확
- balance_gain 부호가 시나리오에 맞음
"""

from __future__ import annotations

import pytest

from src.engine import compatibility as compat
from src.engine import relations as rel
from src.engine.schema import FourPillars, Pillar


def make_pillars(
    y: tuple[str, str],
    m: tuple[str, str],
    d: tuple[str, str],
    h: tuple[str, str] | None = None,
) -> FourPillars:
    return FourPillars(
        year=Pillar(gan=y[0], ji=y[1]),
        month=Pillar(gan=m[0], ji=m[1]),
        day=Pillar(gan=d[0], ji=d[1]),
        hour=Pillar(gan=h[0], ji=h[1]) if h else None,
    )


def test_cross_relations_only_cross() -> None:
    """A 내부 관계는 cross에 포함되면 안 됨."""
    # A: 子午沖 내부 (year_ji=子, month_ji=午) — 내부 충
    a = make_pillars(("甲", "子"), ("丙", "午"), ("戊", "辰"), ("庚", "申"))
    # B: 단순한 사주, A와 cross 충 없음
    b = make_pillars(("乙", "丑"), ("丁", "未"), ("己", "巳"), ("辛", "酉"))

    cross = rel.find_cross_relations(a, b)
    # cross 관계의 positions 는 모두 A_ + B_ 가 섞여야 함
    for r in cross:
        persons = {p.split("_", 1)[0] for p in r.positions}
        assert persons == {"A", "B"}, f"cross가 아닌 관계 검출: {r}"


def test_cross_chung_detected() -> None:
    """A의 일지(子)와 B의 일지(午) 충 → cross 검출됨."""
    a = make_pillars(("甲", "寅"), ("丙", "辰"), ("戊", "子"), ("庚", "申"))
    b = make_pillars(("乙", "卯"), ("丁", "巳"), ("己", "午"), ("辛", "酉"))
    cross = rel.find_cross_relations(a, b)
    chungs = [r for r in cross if r.type == rel.RelationType.JI_JI_CHUNG]
    assert any(
        set(r.members) == {"子", "午"} and "A_day_ji" in r.positions and "B_day_ji" in r.positions
        for r in chungs
    )


def test_day_master_pair_bidirectional() -> None:
    """일간 십성: 丙(火) 일간 vs 壬(水) 일간 → 壬은 丙에게 편관(같은 음양, 극당함)."""
    # 丙午 vs 壬子
    a = make_pillars(("甲", "寅"), ("丙", "午"), ("丙", "午"), ("甲", "午"))
    b = make_pillars(("壬", "子"), ("壬", "子"), ("壬", "子"), ("壬", "子"))
    res = compat.analyze_pair(a, b)
    # 丙 → 壬: 壬은 水이고 丙은 火, 水가 火를 극(controls_me), 음양 같음(陽陽) → 편관
    assert res.day_master_pair.a_to_b.value == "편관"
    # 壬 → 丙: 壬은 水, 丙은 火, 水가 火를 극(i_control), 음양 같음 → 편재
    assert res.day_master_pair.b_to_a.value == "편재"


def test_element_dynamic_saeng() -> None:
    """A 木 일간 vs B 火 일간 → A생B (木生火)."""
    a = make_pillars(("甲", "寅"), ("乙", "卯"), ("甲", "寅"), ("乙", "卯"))
    b = make_pillars(("丙", "午"), ("丁", "巳"), ("丙", "午"), ("丁", "巳"))
    res = compat.analyze_pair(a, b)
    assert res.day_master_pair.dynamic.value == "A생B"


def test_element_dynamic_bihwa() -> None:
    a = make_pillars(("甲", "寅"), ("乙", "卯"), ("甲", "寅"), ("乙", "卯"))
    b = make_pillars(("乙", "卯"), ("甲", "寅"), ("乙", "卯"), ("甲", "寅"))
    res = compat.analyze_pair(a, b)
    assert res.day_master_pair.dynamic.value == "비화"


def test_balance_gain_positive_when_complementary() -> None:
    """A는 木火 편중, B는 金水 편중 → 합산 시 균형 개선."""
    a = make_pillars(("甲", "寅"), ("乙", "卯"), ("丙", "午"), ("丁", "巳"))
    b = make_pillars(("庚", "申"), ("辛", "酉"), ("壬", "子"), ("癸", "亥"))
    res = compat.analyze_pair(a, b)
    assert res.element_combined.balance_gain > 0.0


def test_balance_gain_zero_or_negative_when_same() -> None:
    """A·B가 모두 木火 일변도 → 합산해도 균형 안 좋아짐."""
    a = make_pillars(("甲", "寅"), ("乙", "卯"), ("丙", "午"), ("丁", "巳"))
    b = make_pillars(("甲", "寅"), ("乙", "卯"), ("丙", "午"), ("丁", "巳"))
    res = compat.analyze_pair(a, b)
    assert res.element_combined.balance_gain <= 0.0


def test_notes_nonempty() -> None:
    a = make_pillars(("甲", "寅"), ("丙", "辰"), ("戊", "子"), ("庚", "申"))
    b = make_pillars(("乙", "卯"), ("丁", "巳"), ("己", "午"), ("辛", "酉"))
    res = compat.analyze_pair(a, b)
    # 최소 일간 관계 + 오행 방향 2개는 항상 들어감
    assert len(res.notes) >= 2


def test_counts_consistent() -> None:
    a = make_pillars(("甲", "寅"), ("丙", "辰"), ("戊", "子"), ("庚", "申"))
    b = make_pillars(("乙", "卯"), ("丁", "巳"), ("己", "午"), ("辛", "酉"))
    res = compat.analyze_pair(a, b)
    hap_n = sum(
        1
        for r in res.cross_relations
        if r.type
        in (
            rel.RelationType.CHEON_GAN_HAP,
            rel.RelationType.JI_JI_YUK_HAP,
            rel.RelationType.JI_JI_SAM_HAP,
            rel.RelationType.JI_JI_BANG_HAP,
        )
    )
    conflict_n = sum(
        1
        for r in res.cross_relations
        if r.type
        in (
            rel.RelationType.JI_JI_CHUNG,
            rel.RelationType.JI_JI_HYEONG,
            rel.RelationType.JI_JI_HAE,
            rel.RelationType.JI_JI_PA,
        )
    )
    assert res.strong_bonds_count == hap_n
    assert res.conflicts_count == conflict_n


@pytest.mark.parametrize(
    "a_pair,b_pair,expected",
    [
        # 같은 오행 → 비화
        (("甲", "寅"), ("甲", "寅"), "비화"),
        # 木·火 → A생B
        (("甲", "寅"), ("丙", "午"), "A생B"),
        # 火·木 → B생A
        (("丙", "午"), ("甲", "寅"), "B생A"),
        # 木·土 → A극B
        (("甲", "寅"), ("戊", "辰"), "A극B"),
        # 土·木 → B극A
        (("戊", "辰"), ("甲", "寅"), "B극A"),
    ],
)
def test_all_dynamics(
    a_pair: tuple[str, str], b_pair: tuple[str, str], expected: str
) -> None:
    a = make_pillars(("甲", "子"), ("甲", "子"), a_pair, ("甲", "子"))
    b = make_pillars(("乙", "丑"), ("乙", "丑"), b_pair, ("乙", "丑"))
    res = compat.analyze_pair(a, b)
    assert res.day_master_pair.dynamic.value == expected

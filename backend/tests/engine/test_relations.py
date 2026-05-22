"""합·충·형·해·파 모듈 검증 테스트 (TDD — 구현 전 작성).

default 처리(학설 차 명시):
- 삼합/방합: 3자 완전 성립만 검출(반합·부분 비검출)
- 자형(辰辰·午午·酉酉·亥亥): 형으로 포함
- 합화(合化) 성립: 미구현(NotImplementedError)
"""

import pytest

from src.engine import relations as rel
from src.engine.schema import FourPillars, Pillar

RT = rel.RelationType
EVEN_JI = set("子寅辰午申戌")
EVEN_GAN = set("甲丙戊庚壬")


def _gan_for_ji(ji: str) -> str:
    """지지 음양에 맞는 임의 천간(유효 간지 구성용)."""
    return "甲" if ji in EVEN_JI else "乙"


def pj(ji: str) -> Pillar:
    return Pillar(gan=_gan_for_ji(ji), ji=ji)


def pg(gan: str) -> Pillar:
    return Pillar(gan=gan, ji=("子" if gan in EVEN_GAN else "丑"))


def member_sets(relations) -> set[frozenset[str]]:
    return {frozenset(r.members) for r in relations}


# ── 천간합 5쌍 ────────────────────────────────────────────────
CHEON_GAN_HAP = [("甲", "己"), ("乙", "庚"), ("丙", "辛"), ("丁", "壬"), ("戊", "癸")]


@pytest.mark.parametrize("g1,g2", CHEON_GAN_HAP)
def test_cheon_gan_hap(g1, g2):
    pillars = FourPillars(year=pg(g1), month=pg(g2), day=pg("丁"))
    rels = rel.find_relations_by_type(pillars, RT.CHEON_GAN_HAP)
    assert frozenset({g1, g2}) in member_sets(rels)


# ── 지지 육합 6쌍 ─────────────────────────────────────────────
YUK_HAP = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]


@pytest.mark.parametrize("a,b", YUK_HAP)
def test_yuk_hap(a, b):
    pillars = FourPillars(year=pj(a), month=pj(b), day=pj(a))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_YUK_HAP)
    assert frozenset({a, b}) in member_sets(rels)


# ── 삼합 4조 (완전 성립만) ────────────────────────────────────
SAM_HAP = [("申", "子", "辰"), ("亥", "卯", "未"), ("寅", "午", "戌"), ("巳", "酉", "丑")]


@pytest.mark.parametrize("a,b,c", SAM_HAP)
def test_sam_hap_full(a, b, c):
    pillars = FourPillars(year=pj(a), month=pj(b), day=pj(c))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_SAM_HAP)
    assert frozenset({a, b, c}) in member_sets(rels)


def test_sam_hap_partial_not_detected():
    # 申子만(반합) → 비검출
    pillars = FourPillars(year=pj("申"), month=pj("子"), day=pg("丁"))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_SAM_HAP)
    assert rels == []


# ── 방합 4조 (완전 성립만) ────────────────────────────────────
BANG_HAP = [("寅", "卯", "辰"), ("巳", "午", "未"), ("申", "酉", "戌"), ("亥", "子", "丑")]


@pytest.mark.parametrize("a,b,c", BANG_HAP)
def test_bang_hap_full(a, b, c):
    pillars = FourPillars(year=pj(a), month=pj(b), day=pj(c))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_BANG_HAP)
    assert frozenset({a, b, c}) in member_sets(rels)


def test_bang_hap_partial_not_detected():
    pillars = FourPillars(year=pj("寅"), month=pj("卯"), day=pg("丁"))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_BANG_HAP)
    assert rels == []


# ── 충 6쌍 ────────────────────────────────────────────────────
CHUNG = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]


@pytest.mark.parametrize("a,b", CHUNG)
def test_chung(a, b):
    pillars = FourPillars(year=pj(a), month=pj(b), day=pj(a))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_CHUNG)
    assert frozenset({a, b}) in member_sets(rels)


# ── 형 ────────────────────────────────────────────────────────
def test_hyeong_samhyeong_insasin():
    pillars = FourPillars(year=pj("寅"), month=pj("巳"), day=pj("申"))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_HYEONG)
    assert frozenset({"寅", "巳", "申"}) in member_sets(rels)


def test_hyeong_samhyeong_chulsulmi():
    pillars = FourPillars(year=pj("丑"), month=pj("戌"), day=pj("未"))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_HYEONG)
    assert frozenset({"丑", "戌", "未"}) in member_sets(rels)


def test_hyeong_sanghyeong_jamyo():
    pillars = FourPillars(year=pj("子"), month=pj("卯"), day=pj("子"))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_HYEONG)
    assert frozenset({"子", "卯"}) in member_sets(rels)


@pytest.mark.parametrize("ji", ["辰", "午", "酉", "亥"])
def test_hyeong_jahyeong(ji):
    pillars = FourPillars(year=pj(ji), month=pj(ji), day=pj("子"))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_HYEONG)
    assert any(r.members == (ji, ji) for r in rels)


# ── 해 6쌍 ────────────────────────────────────────────────────
HAE = [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]


@pytest.mark.parametrize("a,b", HAE)
def test_hae(a, b):
    pillars = FourPillars(year=pj(a), month=pj(b), day=pj(a))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_HAE)
    assert frozenset({a, b}) in member_sets(rels)


# ── 파 6쌍 ────────────────────────────────────────────────────
PA = [("子", "酉"), ("卯", "午"), ("巳", "申"), ("寅", "亥"), ("丑", "辰"), ("戌", "未")]


@pytest.mark.parametrize("a,b", PA)
def test_pa(a, b):
    pillars = FourPillars(year=pj(a), month=pj(b), day=pj(a))
    rels = rel.find_relations_by_type(pillars, RT.JI_JI_PA)
    assert frozenset({a, b}) in member_sets(rels)


# ── find_all_relations 통합 3건 ──────────────────────────────
def test_find_all_cheon_gan_hap_and_yuk_hap():
    # 甲(년간)·己(월간) 천간합, 子(년지)·丑(월지) 육합
    pillars = FourPillars(year=Pillar(gan="甲", ji="子"), month=Pillar(gan="己", ji="丑"),
                          day=Pillar(gan="丙", ji="寅"))
    rels = rel.find_all_relations(pillars)
    types = {(r.type, frozenset(r.members)) for r in rels}
    assert (RT.CHEON_GAN_HAP, frozenset({"甲", "己"})) in types
    assert (RT.JI_JI_YUK_HAP, frozenset({"子", "丑"})) in types


def test_find_all_chung():
    pillars = FourPillars(year=Pillar(gan="甲", ji="子"), month=Pillar(gan="戊", ji="午"),
                          day=Pillar(gan="乙", ji="丑"))
    assert (RT.JI_JI_CHUNG, frozenset({"子", "午"})) in {
        (r.type, frozenset(r.members)) for r in rel.find_all_relations(pillars)
    }


def test_find_all_sam_hap():
    pillars = FourPillars(year=Pillar(gan="甲", ji="申"), month=Pillar(gan="甲", ji="子"),
                          day=Pillar(gan="戊", ji="辰"))
    assert (RT.JI_JI_SAM_HAP, frozenset({"申", "子", "辰"})) in {
        (r.type, frozenset(r.members)) for r in rel.find_all_relations(pillars)
    }


# ── 동일 position 중복 검출 방지 ─────────────────────────────
def test_no_duplicate_for_same_positions():
    pillars = FourPillars(year=pj("子"), month=pj("午"), day=pj("丑"))
    chung = rel.find_relations_by_type(pillars, RT.JI_JI_CHUNG)
    # 子午 충은 (year,month) 한 조합으로 정확히 1번만
    assert len(chung) == 1
    assert chung[0].members == ("子", "午")
    assert chung[0].positions == ("year_ji", "month_ji")


# ── has_chung / has_hap ──────────────────────────────────────
def test_has_chung_and_has_hap():
    pillars = FourPillars(year=Pillar(gan="甲", ji="子"), month=Pillar(gan="戊", ji="午"),
                          day=Pillar(gan="乙", ji="丑"))
    assert rel.has_chung(pillars, "year_ji") is True
    assert rel.has_chung(pillars, "day_ji") is False  # 丑은 충 없음
    assert rel.has_hap(pillars, "year_ji") is True  # 子丑 육합
    assert rel.has_hap(pillars, "month_ji") is False  # 午는 합 없음


# ── 합화 미구현 ───────────────────────────────────────────────
def test_detect_hap_hwa_not_implemented():
    pillars = FourPillars(year=Pillar(gan="甲", ji="子"), month=Pillar(gan="己", ji="丑"),
                          day=Pillar(gan="丙", ji="寅"))
    hap = rel.find_relations_by_type(pillars, RT.CHEON_GAN_HAP)[0]
    with pytest.raises(NotImplementedError):
        rel.detect_hap_hwa(pillars, hap)

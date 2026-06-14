"""용신 모듈 검증 테스트 (잠정).

⚠ 자문위원 정책 8(YongsinMethod) 미확정. EOKBU 통설 default의 구조적
동작(라벨 도메인·신강↔신약 분기·희기구 일관성)만 검증.
"""

from src.engine import yongsin
from src.engine.constants import Ohaeng
from src.engine.schema import FourPillars, Pillar


def _p(g: str, j: str) -> Pillar:
    return Pillar(gan=g, ji=j)


SIN_GANG = FourPillars(  # 일간 壬(水), 사주 전체 水 → 신강
    year=_p("壬", "子"), month=_p("壬", "子"), day=_p("壬", "子"), hour=_p("壬", "子")
)
SIN_YAK = FourPillars(  # 일간 壬(水), 火·土로 둘러쌈 → 신약
    year=_p("丙", "午"), month=_p("丙", "午"), day=_p("壬", "戌"), hour=_p("戊", "辰")
)


def test_sin_yak_yongsin_is_parent_element():
    # 일간 壬(水)의 父 = 金. EOKBU 신약 → 용신 = 金
    r = yongsin.derive_yongsin(SIN_YAK)
    assert r.yongsin == Ohaeng.GEUM
    assert r.method == "eokbu"
    assert r.based_on_strength == "신약"
    assert r.confidence == "provisional"


def test_sin_gang_yongsin_hybrid():
    # 壬(水) 신강 + 子월(한겨울 水왕, 火 결핍) → 궁통보감 통설 "壬水 子월 專用丙火".
    # frigid 게이팅: 火가 원국에 결핍(0%)이라 조후(火)가 억부(식상 木)보다 우선.
    r = yongsin.derive_yongsin(SIN_GANG)
    assert r.based_on_strength == "신강"
    assert r.yongsin == Ohaeng.HWA  # 한겨울 壬水 → 조후 火(丙火 온난)
    assert r.method == "johu"


def test_huishin_giishin_consistency():
    # 신약 케이스: 용신 金 → 희신 土(生金), 기신 火(克金), 구신 木(生火→克金의 기신을 돕는)
    r = yongsin.derive_yongsin(SIN_YAK)
    assert r.yongsin == Ohaeng.GEUM
    assert r.huishin == Ohaeng.TO   # 土生金
    assert r.gisin == Ohaeng.HWA    # 火克金
    assert r.gushin == Ohaeng.MOK   # 木生火(기신을 도움)


def test_distinct_four_neologisms():
    # 용·희·기·구는 모두 다른 오행이어야 함
    for chart in (SIN_GANG, SIN_YAK):
        r = yongsin.derive_yongsin(chart)
        assert len({r.yongsin, r.huishin, r.gisin, r.gushin}) == 4


def test_deterministic():
    a = yongsin.derive_yongsin(SIN_YAK)
    b = yongsin.derive_yongsin(SIN_YAK)
    assert a == b

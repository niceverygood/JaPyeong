"""신강신약 모듈 검증 테스트 (TDD — 구현 전 작성).

⚠ 잠정(provisional) — 자문위원 정책 7·8 미확정. 본 테스트는 알고리즘의 정확성이
아니라 "구조적 속성"(결정론·임계값·아군 정의·라벨 도메인)을 검증한다.
'정답' 사주에 대한 라벨 단정은 자문위원 검증 케이스 도입 후 추가한다.
"""

import pytest

from src.engine import strength
from src.engine.constants import Ohaeng
from src.engine.schema import FourPillars, Pillar


def _p(g: str, j: str) -> Pillar:
    return Pillar(gan=g, ji=j)


# 일간 壬(水), 모든 자리 水 → 극단적 신강
PURE_ALLY = FourPillars(
    year=_p("壬", "子"), month=_p("壬", "子"), day=_p("壬", "子"), hour=_p("壬", "子")
)
# 일간 壬(水), 모든 자리가 火·土·金 으로 채워져 水 거의 없음 → 극단적 신약
PURE_HOSTILE = FourPillars(
    year=_p("丙", "午"), month=_p("丙", "午"), day=_p("壬", "戌"), hour=_p("戊", "辰")
)
# 균형 있는 분포 (이전 스팟체크용 차트)
BALANCED = FourPillars(
    year=_p("甲", "子"), month=_p("丙", "寅"), day=_p("戊", "辰"), hour=_p("庚", "午")
)


def test_pure_ally_is_sin_gang():
    r = strength.assess_strength(PURE_ALLY)
    assert r.label == "신강"
    assert r.ally_ratio > 0.9
    assert r.deuk_ryeong is True  # 월지 子(水) — 같은 오행
    assert r.confidence == "high"  # ratio>0.9 → 경계서 멀어 명백(신뢰도 high)


def test_pure_hostile_is_sin_yak():
    r = strength.assess_strength(PURE_HOSTILE)
    assert r.label == "신약"
    assert r.ally_ratio < 0.2
    assert r.deuk_ryeong is False  # 월지 午(火) — 일간 水와 무관


def test_ally_ratio_in_range():
    r = strength.assess_strength(BALANCED)
    assert 0.0 <= r.ally_ratio <= 1.0
    assert r.label in ("신강", "신약", "중화")


@pytest.mark.parametrize(
    "pillars,deuk_ji",
    [
        (PURE_ALLY, True),  # 일지 子(水) — 일간 水와 같은 오행
        (PURE_HOSTILE, False),  # 일지 戌(土) — 일간 水를 극함
    ],
)
def test_deuk_ji(pillars, deuk_ji):
    assert strength.assess_strength(pillars).deuk_ji is deuk_ji


def test_components_include_breakdown():
    r = strength.assess_strength(BALANCED)
    # 분포 합이 양수
    assert r.ally_score > 0 or r.hostile_score > 0
    assert r.ally_score + r.hostile_score == pytest.approx(r.total_score)


def test_deterministic():
    a = strength.assess_strength(BALANCED)
    b = strength.assess_strength(BALANCED)
    assert a == b


def test_ally_definition_includes_same_and_parent():
    # 일간 오행 + 부모(인성) 오행이 아군. 자식·재성·관성은 적군.
    r = strength.assess_strength(PURE_ALLY)
    # 一律 水일 때 아군에는 水(비겁) + 金(인성) 포함 — 적군 자리 = 木·火·土
    assert Ohaeng.SU in r.ally_elements
    assert Ohaeng.GEUM in r.ally_elements

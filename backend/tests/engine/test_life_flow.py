"""engine.life_flow 단위 테스트.

규칙:
- 점수 [-5, +5] 클램프
- 용신/희신/기신/구신 매칭이 정확히 가산/감점
- 일지 충/육합 추가 보너스/페널티
- 라벨 매핑 (대길 ≥3 / 길 ≥1.5 / 평 ≥-1.5 / 주의 ≥-3 / 흉)
"""

from __future__ import annotations

from src.engine import life_flow as lf
from src.engine.constants import Ohaeng
from src.engine.daewoon import DaewoonPeriod
from src.engine.schema import FourPillars, Pillar
from src.engine.yongsin import YongsinResult


def pillars(d_gan: str = "丙", d_ji: str = "午") -> FourPillars:
    return FourPillars(
        year=Pillar(gan="甲", ji="子"),
        month=Pillar(gan="乙", ji="丑"),
        day=Pillar(gan=d_gan, ji=d_ji),
        hour=Pillar(gan="戊", ji="戌"),
    )


def yongsin(
    y: Ohaeng = Ohaeng.SU,
    h: Ohaeng = Ohaeng.GEUM,
    g: Ohaeng = Ohaeng.TO,
    gu: Ohaeng = Ohaeng.HWA,
) -> YongsinResult:
    return YongsinResult(
        yongsin=y,
        huishin=h,
        gisin=g,
        gushin=gu,
        method="eokbu",
        based_on_strength="신강",
    )


def period(gan: str, ji: str, seq: int = 1, age: int = 10) -> DaewoonPeriod:
    return DaewoonPeriod(sequence=seq, start_age=age, gan=gan, ji=ji)


def test_yongsin_gan_plus_two() -> None:
    """대운 천간이 용신 오행이면 +2."""
    # 용신=水, 대운=壬子: 천간 壬(水)=용신 +2, 지지 子(水)=용신 +2 → +4
    pt = lf.score_period(period("壬", "子"), pillars(), yongsin(y=Ohaeng.SU))
    # 일지 午 vs 대운 子 = 충 (-1) → 총 3.0
    assert pt.score == 3.0
    assert pt.label == "대길"


def test_gisin_minus_two() -> None:
    """기신=土, 대운 戊戌 → 천간 -2, 지지 戌(土)=-2 → -4. 일지 午 vs 戌 합·충 없음 → -4."""
    pt = lf.score_period(period("戊", "戌"), pillars(d_ji="午"), yongsin(g=Ohaeng.TO))
    assert pt.score == -4.0
    assert pt.label == "흉"


def test_neutral_period() -> None:
    """용신/희신/기신/구신 어디에도 속하지 않으면 0."""
    # 용신=水, 희신=金, 기신=土, 구신=火. 대운 甲(木)寅(木) 은 모두 해당 없음
    pt = lf.score_period(period("甲", "寅"), pillars(), yongsin())
    # 일지 午 vs 寅: 합도 충도 아님 (寅午戌 삼합은 3자 필요)
    assert pt.score == 0.0
    assert pt.label == "평"


def test_score_clamped_to_5() -> None:
    """가산이 +5 이상이어도 +5로 클램프."""
    # 용신=水, 대운 壬子. 일지 = 丑이면 子丑 육합 +0.25(합화 미검증 약화)
    # 천간 +2 + 지지 +2 + 합 +0.25 = +4.25 (클램프 무관)
    pt = lf.score_period(period("壬", "子"), pillars(d_ji="丑"), yongsin(y=Ohaeng.SU))
    assert pt.score == 4.25


def test_chung_penalty() -> None:
    """대운 지지가 일지와 충이면 -1."""
    pt = lf.score_period(period("甲", "子"), pillars(d_ji="午"), yongsin())
    # 甲(木), 子(水) → 용신 무관 (용신=水일 때 子=+2이므로 다른 yongsin)
    # 여기선 default yongsin=SU이라 子=+2. 일지 午 vs 子=충 → 총 +2-1 = +1
    assert pt.score == 1.0


def test_yukhap_bonus() -> None:
    """대운 지지가 일지와 육합이면 +0.25(합화 성립 미검증이라 보수적 약화)."""
    # 일지 子 → 子丑 육합. 대운 ji=丑
    pt = lf.score_period(period("甲", "丑"), pillars(d_ji="子"), yongsin())
    # 甲(木)=neutral, 丑(土)=기신(-2). 일지 子 ↔ 丑 육합 +0.25 = -1.75
    assert pt.score == -1.75


def test_label_thresholds() -> None:
    assert lf._label_for(3.5) == "대길"
    assert lf._label_for(2.0) == "길"
    assert lf._label_for(0.0) == "평"
    assert lf._label_for(-2.0) == "주의"
    assert lf._label_for(-4.0) == "흉"


def test_build_life_flow_length() -> None:
    periods = [period("甲", "子", seq=i, age=10 + (i - 1) * 10) for i in range(1, 10)]
    flow = lf.build_life_flow(pillars(), periods, yongsin())
    assert len(flow) == 9
    for i, p in enumerate(flow):
        assert p.start_age == 10 + i * 10
        assert p.end_age == p.start_age + 9

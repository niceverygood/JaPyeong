"""일진(日辰) 알림 — 사용자 사주 + 오늘 일진 → 짧은 푸시 메시지.

자평 정체성 가드레일 (단정·공포 자극 금지):
  - "주의 깊게 볼 구간" 톤 (위협 X)
  - 부정 통변에 항상 대응 가이드 동봉
  - "할 가능성", "흐름" 등 절제 어법
  - 단정형·100%·놓치면 어휘 0건

점수 (-5..+5):
  - 일운 천간 vs 사주 일간 → 십성 (정관/정인 = +1, 편관/편인 = -1)
  - 일운 지지 vs 사주 일지 → 합(+0.5) / 충(-1)
  - 동일 일지 (伏吟) → -0.5

메시지 카테고리:
  - 대길 (>=2): 책임·결정·교섭에 좋은 흐름
  - 길 (>=0.5): 평소대로 흘러가는 날
  - 평 (-0.5~0.5): 평이한 흐름
  - 주의 (-2): 변화·결단 일단 미루기 좋은 날
  - 흉 (<-2): 큰 결정·서명·계약 자제

순수 함수, 결정론적.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.engine import sewoon
from src.engine.ganji import gan_ohaeng
from src.engine.schema import FourPillars, Pillar
from src.engine.ten_gods import TenGod, get_ten_god


@dataclass(frozen=True, slots=True)
class DailyFortune:
    """일진 알림 데이터."""

    date: date
    day_pillar: Pillar           # 오늘 일운 (天干 + 地支)
    ten_god: TenGod              # 일운 천간이 일간 기준 십성
    score: float                 # -5..+5
    label: str                   # 대길/길/평/주의/흉
    title: str                   # 푸시 제목 (30자 이내)
    body: str                    # 푸시 본문 (80자 이내)
    suggested_areas: list[str]   # "주의 깊게 볼 영역" 0~2개


# ── 십성별 디폴트 톤 (자평 정체성 — 단정 X, 흐름 O) ────────
_TEN_GOD_NOTE: dict[TenGod, tuple[str, float]] = {
    TenGod.JEONG_GWAN: ("책임·규범의 흐름", +1.0),
    TenGod.PYEON_GWAN: ("결단·압박 흐름", -0.5),
    TenGod.JEONG_IN: ("배움·인연·후원 흐름", +1.0),
    TenGod.PYEON_IN: ("성찰·내면 흐름", +0.3),
    TenGod.SIK_SIN: ("표현·여유 흐름", +0.5),
    TenGod.SANG_GWAN: ("재기·반항 흐름 — 큰 결정 신중", -0.5),
    TenGod.JEONG_JAE: ("정당한 재물 흐름", +0.3),
    TenGod.PYEON_JAE: ("기회·유동 흐름", +0.3),
    TenGod.BI_GYEON: ("자기 중심·동료 흐름", +0.5),
    TenGod.GYEOP_JAE: ("경쟁·재 손실 가능", -0.5),
}


# ── 일지 합·충 매핑 ─────────────────────────────────────
_YUKHAP = {
    frozenset(p) for p in [
        ("子", "丑"), ("寅", "亥"), ("卯", "戌"),
        ("辰", "酉"), ("巳", "申"), ("午", "未"),
    ]
}
_CHUNG = {
    frozenset(p) for p in [
        ("子", "午"), ("丑", "未"), ("寅", "申"),
        ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
    ]
}


_LABEL_THRESHOLDS = (
    (2.0, "대길"),
    (0.5, "길"),
    (-0.5, "평"),
    (-2.0, "주의"),
)


def _label_for(score: float) -> str:
    for threshold, label in _LABEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "흉"


def _ji_relation(day_p: str, natal_p: str) -> tuple[float, str]:
    """일운 지지 vs 사주 일지 관계 → (점수, 설명)."""
    if day_p == natal_p:
        return -0.5, "복음(伏吟) — 평소 답답할 수 있는 날"
    pair = frozenset((day_p, natal_p))
    if pair in _CHUNG:
        return -1.0, f"일지({natal_p})와 충(沖) — 변동 신호"
    if pair in _YUKHAP:
        return +0.5, f"일지({natal_p})와 육합 — 화합 흐름"
    return 0.0, ""


def _suggested_areas(ten_god: TenGod, score: float) -> list[str]:
    """오늘 '주의 깊게 볼 영역' (위협이 아닌 점검 프레임)."""
    areas: list[str] = []
    if ten_god in (TenGod.JEONG_GWAN, TenGod.PYEON_GWAN):
        areas.append("책임·계약·공직 흐름")
    if ten_god in (TenGod.JEONG_JAE, TenGod.PYEON_JAE):
        areas.append("재정·소비·투자")
    if ten_god in (TenGod.JEONG_IN, TenGod.PYEON_IN):
        areas.append("학습·자기 점검")
    if ten_god in (TenGod.SIK_SIN, TenGod.SANG_GWAN):
        areas.append("표현·관계")
    if score <= -2.0:
        # 흉인 날엔 대응 가이드 동봉 (자평 가드레일 #5)
        areas.append("큰 결정·서명·계약 자제 권장")
    return areas[:2]  # 푸시 길이 제한


def _compose_message(
    label: str, ten_god: TenGod, score: float,
    ji_note: str,
) -> tuple[str, str]:
    """자평 정체성 톤 메시지 생성. (title, body) 반환.

    원칙:
    - "할 것이다" 단정형 X
    - "놓치면 손해" 공포 자극 X
    - "주의 깊게 볼" 프레임 OK
    """
    god_note, _ = _TEN_GOD_NOTE.get(ten_god, ("평이한 흐름", 0.0))

    if label == "대길":
        title = f"오늘은 좋은 흐름 — {ten_god.value}"
        body = f"{god_note}이 두드러집니다. 점검해 둘 결정이 있으면 좋은 날."
    elif label == "길":
        title = f"오늘 흐름 — {ten_god.value}"
        body = f"{god_note}으로 흐릅니다. 평소처럼."
    elif label == "평":
        title = "오늘은 평이한 흐름"
        body = "특별히 두드러진 신호 없음. 평소대로 운영."
    elif label == "주의":
        title = "주의 깊게 — 신중히 볼 흐름"
        # 항상 신중 가이드 동봉 (자평 가드 #5)
        body = (
            f"{god_note}. {ji_note}. "
            "큰 결정은 다음 흐름으로 미루셔도 좋습니다."
        ).replace(".. ", ". ")
    else:  # 흉
        title = "오늘은 차분히 — 큰 결정 자제"
        body = (
            f"{ji_note or god_note}. "
            "서명·계약·과감한 결단은 흐름이 부드러워질 때까지 미루세요."
        )

    # 길이 제한 (푸시 표준)
    return title[:30], body[:80]


def compute_daily_fortune(
    natal: FourPillars,
    target_date: date,
) -> DailyFortune:
    """사주 + 날짜 → 일진 알림.

    Args:
        natal: 사용자 사주 (FourPillars)
        target_date: 알림 대상 날짜

    Returns:
        DailyFortune — 푸시 메시지에 필요한 모든 필드
    """
    day_pillar = sewoon.il_un(target_date)
    ten_god = get_ten_god(natal.day.gan, day_pillar.gan)
    _ = gan_ohaeng(day_pillar.gan)  # 유효성 조기 검증

    # 점수 계산
    score = 0.0
    _, god_score = _TEN_GOD_NOTE.get(ten_god, ("", 0.0))
    score += god_score

    ji_score, ji_note = _ji_relation(day_pillar.ji, natal.day.ji)
    score += ji_score

    # 클램프
    score = max(-5.0, min(5.0, round(score, 2)))
    label = _label_for(score)
    title, body = _compose_message(label, ten_god, score, ji_note)
    areas = _suggested_areas(ten_god, score)

    return DailyFortune(
        date=target_date,
        day_pillar=day_pillar,
        ten_god=ten_god,
        score=score,
        label=label,
        title=title,
        body=body,
        suggested_areas=areas,
    )

"""코인 카탈로그 — 충전팩 + 단건 상품의 단일 출처(SSOT).

가격/보너스/코인 환산을 코드에 고정한다(DB 시드 불필요, 모바일 iap SKU 와 1:1).
환산: 1 coin = 1 KRW. 충전팩은 결제액만큼 코인 + 보너스 코인 별도 적립.
스토어 인앱결제(consumable) product_id 가 곧 충전팩 코드다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChargePack:
    code: str          # IAP consumable product_id 와 동일
    price_krw: int     # 결제 금액
    coins: int         # 결제로 적립되는 기본 코인 (= price_krw)
    bonus: int         # 추가 보너스 코인
    label: str

    @property
    def total_coins(self) -> int:
        return self.coins + self.bonus


@dataclass(frozen=True, slots=True)
class SpendItem:
    code: str
    cost: int          # 차감 코인
    label: str
    kind: str          # saju_deep | consult | decision | report — 콘텐츠 생성 분기
    description: str


# ── 충전팩 (충전액↑ 보너스↑ — 미사용 잔액 락인) ──────────────
CHARGE_PACKS: dict[str, ChargePack] = {
    p.code: p
    for p in (
        ChargePack("coin_10000", 10_000, 10_000, 200, "1만 코인 (+2%)"),
        ChargePack("coin_30000", 30_000, 30_000, 900, "3만 코인 (+3%)"),
        ChargePack("coin_50000", 50_000, 50_000, 2_000, "5만 코인 (+4%)"),
        ChargePack("coin_100000", 100_000, 100_000, 5_000, "10만 코인 (+5%)"),
    )
}

# ── 단건 상품 (고마진 사다리) ────────────────────────────────
SPEND_ITEMS: dict[str, SpendItem] = {
    s.code: s
    for s in (
        SpendItem(
            "saju_deep", 2_900, "명식 정밀 풀이", "saju_deep",
            "내 사주 8자를 심층(고전 인용) 정밀 해석",
        ),
        SpendItem(
            "consult_one", 4_900, "AI 자문 1건 (심층)", "consult",
            "고민 하나를 프리미엄 심층 모델로 자문",
        ),
        SpendItem(
            "decision_ab", 9_900, "결정 도우미 A/B 정밀", "decision",
            "두 선택지를 심층 모델로 정밀 비교",
        ),
        SpendItem(
            "report_yearly", 19_900, "신년·대운 종합 리포트", "report",
            "올해와 다가오는 대운 흐름 종합 리포트",
        ),
    )
}


def get_charge_pack(code: str) -> ChargePack | None:
    return CHARGE_PACKS.get(code)


def get_spend_item(code: str) -> SpendItem | None:
    return SPEND_ITEMS.get(code)

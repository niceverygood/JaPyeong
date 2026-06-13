"""구독 티어 정의 — 단일 출처(SSOT).

한도(TIER_DAILY)·등급(TIER_RANK)·심층모델 분기(DEEP_TIERS)가 모두 여기서 파생된다.
이전에는 rate_limit / user_service / consultation 세 곳에 흩어져 동기화 깨짐 위험이 있었음.
"""

from __future__ import annotations

# 유효 티어 (게스트 포함)
TIER_NAMES: frozenset[str] = frozenset(
    {"anon", "basic", "standard", "premium", "family"}
)

# 활성 구독이 여러 개일 때 최고 등급 선택용 (anon 은 0 취급).
TIER_RANK: dict[str, int] = {"basic": 1, "standard": 2, "premium": 3, "family": 4}

# 심층 모델(opus) 을 받는 티어 — 가격 정당화의 핵심 차별.
DEEP_TIERS: frozenset[str] = frozenset({"premium", "family"})

# 티어별 일일 자문 한도.
TIER_DAILY: dict[str, int] = {
    "anon": 5,        # 비회원/무료
    "basic": 20,
    "standard": 100,
    "premium": 500,
    "family": 500,    # 가족 1인 기준
}

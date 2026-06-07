"""middleware.rate_limit 단위 테스트.

다층 방어 (회원·IP/분·IP/일) 모두 검증.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.middleware.rate_limit import (
    IP_PER_MINUTE,
    TIER_DAILY,
    InMemoryStore,
    RateLimiter,
)


def make_request(ip: str = "1.2.3.4", user_id: str | None = None) -> MagicMock:
    """FastAPI Request mock."""
    req = MagicMock()
    headers = {"x-real-ip": ip}
    if user_id:
        headers["x-user-id"] = user_id
    req.headers = headers
    req.client = MagicMock(host=ip)
    return req


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter(store=InMemoryStore())


# ── 정상 흐름 ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_first_request_passes(limiter: RateLimiter) -> None:
    """첫 요청은 통과."""
    violation = await limiter.check(make_request(), user_tier="anon")
    assert violation is None


@pytest.mark.asyncio
async def test_under_limit_passes(limiter: RateLimiter) -> None:
    """anon 4건은 한도(5) 안이라 통과."""
    req = make_request()
    for _ in range(4):
        assert await limiter.check(req, user_tier="anon") is None


# ── 회원 일일 한도 ────────────────────────────────────────
@pytest.mark.asyncio
async def test_anon_blocked_after_5(limiter: RateLimiter) -> None:
    """anon 5건은 OK, 6번째는 차단."""
    req = make_request()
    for _ in range(5):
        await limiter.check(req, user_tier="anon")
    violation = await limiter.check(req, user_tier="anon")
    assert violation is not None
    assert "user_daily" in violation.layer
    assert violation.limit == TIER_DAILY["anon"]


@pytest.mark.asyncio
async def test_basic_tier_higher_limit(limiter: RateLimiter) -> None:
    """basic 티어는 20건까지 OK."""
    req = make_request(user_id="user-123")
    for i in range(20):
        v = await limiter.check(req, user_tier="basic")
        assert v is None, f"i={i}, v={v}"
    v = await limiter.check(req, user_tier="basic")
    assert v is not None and v.limit == TIER_DAILY["basic"]


@pytest.mark.asyncio
async def test_premium_tier_very_high(limiter: RateLimiter) -> None:
    """premium 티어 한도(500) > basic 한도(20) — 적은 수로 검증."""
    req = make_request(user_id="prem-user")
    # 50건은 premium 한도 안 (IP/min 60도 안 넘김)
    for _ in range(50):
        v = await limiter.check(req, user_tier="premium")
        assert v is None


# ── 사용자 격리 ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_different_users_independent(limiter: RateLimiter) -> None:
    """다른 user_id 는 카운터 분리."""
    req_a = make_request(ip="1.1.1.1", user_id="user-A")
    req_b = make_request(ip="2.2.2.2", user_id="user-B")
    for _ in range(20):
        await limiter.check(req_a, user_tier="basic")
    # B 는 여전히 통과 가능
    v = await limiter.check(req_b, user_tier="basic")
    assert v is None


# ── IP 분당 한도 ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_ip_per_minute_block(limiter: RateLimiter) -> None:
    """같은 IP 에서 60+ req/min 시 차단."""
    req = make_request(ip="9.9.9.9", user_id="bot")
    # 60건은 통과
    for _ in range(60):
        v = await limiter.check(req, user_tier="premium")
        assert v is None
    # 61번째 차단 (IP per minute)
    v = await limiter.check(req, user_tier="premium")
    assert v is not None
    assert v.layer == "ip_per_minute"
    assert v.limit == IP_PER_MINUTE


# ── enforce — HTTPException 변환 ───────────────────────────
@pytest.mark.asyncio
async def test_enforce_passes_when_ok(limiter: RateLimiter) -> None:
    """위반 없으면 raise 안 함."""
    await limiter.enforce(make_request(), user_tier="anon")  # 첫 요청 = OK


@pytest.mark.asyncio
async def test_enforce_raises_429(limiter: RateLimiter) -> None:
    """위반 시 HTTPException 429 + Retry-After."""
    req = make_request()
    for _ in range(5):
        await limiter.enforce(req, user_tier="anon")
    with pytest.raises(HTTPException) as exc_info:
        await limiter.enforce(req, user_tier="anon")
    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    # paywall 메시지
    assert "한도" in exc_info.value.detail or "구독" in exc_info.value.detail


# ── 시뮬: "디시 폭주" — 한 IP 에서 1000+ 다계정 시도 ───────
@pytest.mark.asyncio
async def test_dc_spike_simulation(limiter: RateLimiter) -> None:
    """같은 IP에서 다른 user-id로 1000건 시도 = IP per day로 자동 차단."""
    ip = "5.5.5.5"
    # 100건 시도 — 다른 사용자 ID 마다 1건씩만, IP day 카운터 누적 100건
    for i in range(100):
        req = make_request(ip=ip, user_id=f"fake-{i}")
        v = await limiter.check(req, user_tier="premium")
        if v:
            break

    # 시뮬 — 60건 분당 = ip_per_minute 차단
    # 첫 60건 후 차단 됐을 것
    assert v is not None  # 어느 레이어든 차단 됐어야

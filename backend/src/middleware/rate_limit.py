"""Rate Limit 다층 방어 — 자평 정체성 보험 ❸.

LLM 비용 폭주·봇 어그로·다계정 우회 차단.

레이어 (모두 동시 적용):
  ① 회원 일일 한도 (anon=5, basic=20, std=100, prem=500)
  ② IP 분당 한도 (60 req/min)
  ③ IP 일일 한도 (1,000 req/day)
  ④ (선택) 디바이스 fingerprint — Sprint 5 이후 도입

스토리지 백엔드:
  - InMemoryStore: 단일 프로세스 (Vercel 서버리스 cold start에는 부적합 — 시뮬·테스트용)
  - RedisStore (TODO Sprint 1-2): Upstash Redis 또는 Vercel KV
  - 환경변수 REDIS_URL 이 있으면 Redis, 없으면 InMemory 폴백

위반 시 응답:
  - HTTP 429 + Retry-After 헤더 + JSON {"detail": "...", "retry_after": int}

사용:
    from src.middleware.rate_limit import RateLimiter
    limiter = RateLimiter()  # 환경변수 기반 자동 셋업

    @router.post("/expensive-endpoint")
    async def endpoint(request: Request):
        await limiter.enforce(request, user_tier="anon")
        ...
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

from fastapi import HTTPException, Request

from src.security.jwt_auth import AuthError, decode_token, extract_bearer


def _claims_from_request(request: Request):
    """Authorization bearer JWT → TokenClaims | None.

    토큰이 없거나 검증 실패면 None(게스트 취급). rate limit·tier 해석의 단일 출처.
    """
    token = extract_bearer(request.headers.get("authorization"))
    if not token:
        return None
    try:
        return decode_token(token)
    except AuthError:
        return None


def resolve_tier(request: Request) -> str:
    """요청의 JWT 에서 구독 티어를 추출. 비로그인/무효 토큰은 'anon'."""
    claims = _claims_from_request(request)
    return claims.tier if claims else "anon"


def resolve_user_id(request: Request) -> int | None:
    """요청의 JWT 에서 user_id 추출 (로그 자산화용). 없으면 None."""
    claims = _claims_from_request(request)
    return claims.user_id if claims else None


# ── 티어별 일일 한도 (core.tiers SSOT) ───────────────────
from src.core.tiers import TIER_DAILY  # noqa: E402

IP_PER_MINUTE = 60
IP_PER_DAY = 1000


# ── 스토리지 인터페이스 ─────────────────────────────────────
class CounterStore(Protocol):
    """카운터 스토리지 인터페이스. Redis or InMemory 모두 만족."""

    async def incr(self, key: str, ttl_seconds: int) -> int:
        """key 의 카운터를 1 증가. 첫 호출 시 ttl 설정. 현재 값 반환."""
        ...

    async def get(self, key: str) -> int:
        """현재 카운터 값 (없으면 0)."""
        ...


# ── In-Memory 구현 (단일 프로세스, 테스트·시뮬용) ───────────
@dataclass
class _MemEntry:
    count: int = 0
    expires_at: float = 0.0


class InMemoryStore:
    """프로세스 내 dict 기반. Vercel 서버리스에선 cold start 마다 리셋되므로 운영 부적합."""

    def __init__(self) -> None:
        self._data: dict[str, _MemEntry] = defaultdict(_MemEntry)

    async def incr(self, key: str, ttl_seconds: int) -> int:
        now = time.time()
        entry = self._data[key]
        if entry.expires_at < now:
            entry.count = 0
            entry.expires_at = now + ttl_seconds
        entry.count += 1
        return entry.count

    async def get(self, key: str) -> int:
        now = time.time()
        entry = self._data.get(key)
        if not entry or entry.expires_at < now:
            return 0
        return entry.count


# ── Redis 구현 (TODO Sprint 1-2 인프라 셋업 후) ─────────────
class RedisStore:
    """Upstash Redis or Vercel KV.

    TODO Sprint 1-2:
        - upstash-redis 또는 redis-py 의존성 추가
        - 실제 INCR + EXPIRE 사용
        - 현재는 stub
    """

    def __init__(self, url: str) -> None:
        self.url = url
        # TODO: from upstash_redis import Redis; self.r = Redis.from_env()
        raise NotImplementedError(
            "RedisStore: Sprint 1-2 인프라 셋업 후 구현 "
            "(REDIS_URL 환경변수 + upstash-redis 패키지)."
        )

    async def incr(self, key: str, ttl_seconds: int) -> int:  # pragma: no cover
        raise NotImplementedError

    async def get(self, key: str) -> int:  # pragma: no cover
        raise NotImplementedError


# ── Rate Limiter 본체 ────────────────────────────────────
@dataclass
class RateLimitViolation:
    layer: str
    limit: int
    current: int
    retry_after_seconds: int


class RateLimiter:
    def __init__(self, store: CounterStore | None = None) -> None:
        if store is None:
            url = os.environ.get("REDIS_URL")
            if url:
                self.store = RedisStore(url)  # type: ignore[assignment]
            else:
                self.store = InMemoryStore()  # type: ignore[assignment]
        else:
            self.store = store

    @staticmethod
    def _get_ip(request: Request) -> str:
        # Vercel·CloudFront 헤더 우선
        for header in ("x-real-ip", "x-forwarded-for", "cf-connecting-ip"):
            v = request.headers.get(header)
            if v:
                return v.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    @staticmethod
    def _get_user_id(request: Request) -> str | None:
        # JWT(Authorization bearer) 에서 user_id 추출 — 회원 일일 한도 카운터 식별자.
        uid = resolve_user_id(request)
        if uid is not None:
            return str(uid)
        # 레거시/DEV 폴백 — 프로덕션 제외 + ALLOW_X_USER_ID 일 때만 헤더 허용
        if (
            os.environ.get("ENV", "").strip().lower() != "production"
            and os.environ.get("ALLOW_X_USER_ID", "false").lower() in ("1", "true", "yes")
        ):
            return request.headers.get("x-user-id")
        return None

    async def check(
        self,
        request: Request,
        user_tier: str | None = None,
    ) -> RateLimitViolation | None:
        """위반 시 RateLimitViolation 반환, 통과 시 None.

        user_tier 가 None 이면 요청 JWT 에서 자동 해석(resolve_tier).
        """
        if user_tier is None:
            user_tier = resolve_tier(request)
        ip = self._get_ip(request)
        user_id = self._get_user_id(request)
        now = int(time.time())

        # ── 레이어 ② IP per minute ─────────────────────────
        ip_min_key = f"rl:ip:min:{ip}:{now // 60}"
        n = await self.store.incr(ip_min_key, ttl_seconds=60)
        if n > IP_PER_MINUTE:
            return RateLimitViolation(
                layer="ip_per_minute", limit=IP_PER_MINUTE, current=n,
                retry_after_seconds=60 - (now % 60),
            )

        # ── 레이어 ③ IP per day ────────────────────────────
        ip_day_key = f"rl:ip:day:{ip}:{now // 86400}"
        n = await self.store.incr(ip_day_key, ttl_seconds=86400)
        if n > IP_PER_DAY:
            return RateLimitViolation(
                layer="ip_per_day", limit=IP_PER_DAY, current=n,
                retry_after_seconds=86400 - (now % 86400),
            )

        # ── 레이어 ① 회원 일일 ─────────────────────────────
        tier_limit = TIER_DAILY.get(user_tier, TIER_DAILY["anon"])
        ident = user_id or f"anon:{ip}"
        user_day_key = f"rl:user:day:{ident}:{now // 86400}"
        n = await self.store.incr(user_day_key, ttl_seconds=86400)
        if n > tier_limit:
            return RateLimitViolation(
                layer=f"user_daily_{user_tier}",
                limit=tier_limit, current=n,
                retry_after_seconds=86400 - (now % 86400),
            )

        return None

    async def enforce_ip_only(self, request: Request) -> None:
        """IP 분당/일일 한도만 적용 — 결제 검증처럼 회원 자문 일일 카운터와
        무관해야 하는(그러나 플러딩은 막아야 하는) 엔드포인트용 DoS 가드."""
        ip = self._get_ip(request)
        now = int(time.time())
        for key, ttl, limit, window in (
            (f"rl:ip:min:{ip}:{now // 60}", 60, IP_PER_MINUTE, 60),
            (f"rl:ip:day:{ip}:{now // 86400}", 86400, IP_PER_DAY, 86400),
        ):
            n = await self.store.incr(key, ttl_seconds=ttl)
            if n > limit:
                raise HTTPException(
                    status_code=429,
                    detail="요청이 많아 잠시 후 다시 시도해 주세요.",
                    headers={"Retry-After": str(window - (now % window))},
                )

    async def enforce(self, request: Request, user_tier: str | None = None) -> None:
        """위반 시 HTTPException(429) raise. user_tier=None 이면 JWT 에서 자동 해석."""
        violation = await self.check(request, user_tier)
        if violation is None:
            return
        # 회원 일일 한도 위반 → paywall 안내
        if violation.layer.startswith("user_daily"):
            detail = (
                f"오늘의 자문 한도({violation.limit}회)를 모두 사용하셨습니다. "
                "더 깊은 풀이는 Basic 이상 구독 후 이용 가능합니다."
            )
        else:
            detail = (
                "잠시 후 다시 시도해 주세요. "
                "비정상적인 요청 패턴이 감지되었습니다."
            )
        raise HTTPException(
            status_code=429,
            detail=detail,
            headers={"Retry-After": str(violation.retry_after_seconds)},
        )

    async def remaining_daily(
        self, request: Request, user_tier: str | None = None
    ) -> tuple[int, int]:
        """소비 없이 회원 일일 자문 잔여·한도를 조회. 반환 (remaining, limit).

        카운터를 증가시키지 않고 store.get으로 현재 사용량만 읽는다(전환 UI 표시용).
        enforce 직후 호출하면 이번 요청을 포함한 잔여를 반환한다.
        """
        if user_tier is None:
            user_tier = resolve_tier(request)
        ip = self._get_ip(request)
        user_id = self._get_user_id(request)
        now = int(time.time())
        tier_limit = TIER_DAILY.get(user_tier, TIER_DAILY["anon"])
        ident = user_id or f"anon:{ip}"
        used = await self.store.get(f"rl:user:day:{ident}:{now // 86400}")
        return max(0, tier_limit - used), tier_limit


# 싱글톤 인스턴스 (모듈 로드 시 자동 셋업)
_default_limiter: RateLimiter | None = None


def get_limiter() -> RateLimiter:
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter()
    return _default_limiter

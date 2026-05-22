"""Redis 연결 (캐시·rate limit·무료 사용량 카운터)."""

from redis.asyncio import Redis

from src.core.config import get_settings

_settings = get_settings()

redis_client: Redis = Redis.from_url(_settings.redis_url, decode_responses=True)

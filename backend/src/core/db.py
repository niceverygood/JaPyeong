"""SQLAlchemy async 엔진/세션 — 지연 초기화.

import 시점에 엔진을 만들지 않는다(asyncpg 미설치 환경에서도 ORM 모델
정의·마이그레이션은 가능해야 함). 첫 세션 요청 시에만 엔진 생성.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings


class Base(DeclarativeBase):
    """모든 ORM 모델의 부모."""


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """첫 호출 시 엔진을 만들고 캐시 (asyncpg 등 드라이버 import는 여기서 발생).

    Supabase Supavisor transaction 풀러(:6543) 경유 시 asyncpg prepared
    statement 가 풀링과 충돌하므로 캐시를 끄고 이름을 무작위화한다.
    서버리스에서는 프로세스 내 풀 대신 NullPool — 풀링은 Supavisor 몫.
    """
    url = get_settings().database_url
    kwargs: dict = {"echo": False, "pool_pre_ping": True}
    if "+asyncpg" in url and (":6543" in url or "pooler.supabase.com" in url):
        from uuid import uuid4

        from sqlalchemy.pool import NullPool

        kwargs["poolclass"] = NullPool
        kwargs["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        }
    return create_async_engine(url, **kwargs)


@lru_cache(maxsize=1)
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성으로 사용: `Depends(get_session)`."""
    async with _session_factory()() as session:
        yield session

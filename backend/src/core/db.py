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
    """첫 호출 시 엔진을 만들고 캐시 (asyncpg 등 드라이버 import는 여기서 발생)."""
    url = get_settings().database_url
    return create_async_engine(url, echo=False, pool_pre_ping=True)


@lru_cache(maxsize=1)
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성으로 사용: `Depends(get_session)`."""
    async with _session_factory()() as session:
        yield session

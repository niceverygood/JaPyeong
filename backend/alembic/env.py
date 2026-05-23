"""Alembic 환경 — 동기 엔진으로 마이그레이션 수행.

운영 환경의 .env 또는 셸 환경변수에서 DATABASE_URL을 읽는다.
런타임 코드는 asyncpg(SQLAlchemy async)를 쓰지만, 마이그레이션은
동기 드라이버(psycopg2/psycopg)로 실행하는 게 표준이므로 +asyncpg/+psycopg
prefix를 정규화한다.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.core.db import Base  # noqa: F401
from src.models import db_models  # noqa: F401  — 메타데이터에 모델 등록

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _resolve_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL 환경변수 미설정 — 마이그레이션 실행 불가")
    # 비동기 드라이버 prefix 제거 (마이그레이션은 동기로)
    return url.replace("+asyncpg", "").replace("+psycopg", "")


config.set_main_option("sqlalchemy.url", _resolve_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

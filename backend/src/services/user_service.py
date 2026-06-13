"""회원 가입·로그인·탈퇴 서비스.

DB 의존 — DATABASE_URL 설정 환경에서만 실 동작.
미설정 환경에서는 raise (회원 기능은 인프라 없이 불가).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from src.security.jwt_auth import (
    create_access_token,
    hash_password,
    verify_password,
)


class UserServiceError(Exception):
    """회원 가입·로그인·탈퇴 도메인 에러 — 사용자에게 노출 가능."""


class DatabaseUnavailableError(UserServiceError):
    """DB 미설정/장애 — 운영 에러. 사용자에게 인프라명 노출 X.

    라우터에서 잡아 503 + generic 메시지로 변환.
    """


def _db_required() -> None:
    if not os.environ.get("DATABASE_URL"):
        raise DatabaseUnavailableError("DATABASE_URL 미설정")


async def signup(
    email: str,
    password: str | None = None,
    name: str | None = None,
    phone: str | None = None,
    oauth_provider: str | None = None,
    oauth_subject: str | None = None,
    marketing_consent: bool = False,
) -> dict[str, Any]:
    """신규 회원 가입.

    이메일 + 비밀번호 또는 OAuth(provider+subject) 둘 중 하나 필수.

    Returns:
        {user_id, token, tier}
    Raises:
        UserServiceError: 이메일 중복 / 입력 오류
    """
    _db_required()
    if not (password or (oauth_provider and oauth_subject)):
        raise UserServiceError("비밀번호 또는 OAuth 자격증명 필요")

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import User

    session: AsyncSession
    async with _session_factory()() as session:
        # 이메일 중복 체크
        existing = (await session.execute(
            select(User).where(User.email == email),
        )).scalar_one_or_none()
        if existing:
            raise UserServiceError("이미 가입된 이메일")

        # OAuth 중복 체크 (provider+subject unique)
        if oauth_provider and oauth_subject:
            existing_oauth = (await session.execute(
                select(User).where(
                    User.oauth_provider == oauth_provider,
                    User.oauth_subject == oauth_subject,
                ),
            )).scalar_one_or_none()
            if existing_oauth:
                raise UserServiceError("이미 가입된 OAuth 계정")

        now = datetime.now(UTC)
        user = User(
            email=email,
            password_hash=hash_password(password) if password else None,
            oauth_provider=oauth_provider,
            oauth_subject=oauth_subject,
            name=name,
            phone=phone,
            created_at=now,
            last_login_at=now,
            is_active=True,
            marketing_consent=marketing_consent,
            marketing_consent_at=now if marketing_consent else None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = create_access_token(user.id, tier="anon")
        return {"user_id": user.id, "token": token, "tier": "anon"}


async def login_with_password(email: str, password: str) -> dict[str, Any]:
    """이메일 + 비밀번호 로그인.

    Returns: {user_id, token, tier}
    """
    _db_required()
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import User

    session: AsyncSession
    async with _session_factory()() as session:
        user = (await session.execute(
            select(User).where(
                User.email == email,
                User.is_active,
                User.deleted_at.is_(None),
            ),
        )).scalar_one_or_none()

        # 타이밍 공격 방지: 비밀번호 검증을 항상 실행
        if user and user.password_hash:
            ok = verify_password(password, user.password_hash)
        else:
            verify_password("dummy", "$2b$12$" + "x" * 53)  # constant-time dummy
            ok = False

        if not user or not ok:
            raise UserServiceError("이메일 또는 비밀번호가 올바르지 않습니다.")

        user.last_login_at = datetime.now(UTC)
        await session.commit()
        token = create_access_token(user.id, tier=_user_tier(user))
        return {"user_id": user.id, "token": token, "tier": _user_tier(user)}


async def login_with_oauth(
    oauth_provider: str,
    oauth_subject: str,
    email: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """카카오·애플·구글 OAuth 로그인 (없으면 자동 가입).

    Returns: {user_id, token, tier, is_new}
    """
    _db_required()
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import User

    session: AsyncSession
    async with _session_factory()() as session:
        user = (await session.execute(
            select(User).where(
                User.oauth_provider == oauth_provider,
                User.oauth_subject == oauth_subject,
                User.deleted_at.is_(None),
            ),
        )).scalar_one_or_none()
        is_new = False

        if user is None:
            # 신규 가입
            if not email:
                raise UserServiceError(
                    f"{oauth_provider} 첫 로그인 — email 필요",
                )
            now = datetime.now(UTC)
            user = User(
                email=email,
                oauth_provider=oauth_provider,
                oauth_subject=oauth_subject,
                name=name,
                created_at=now,
                last_login_at=now,
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            is_new = True
        else:
            user.last_login_at = datetime.now(UTC)
            await session.commit()

        token = create_access_token(user.id, tier=_user_tier(user))
        return {
            "user_id": user.id,
            "token": token,
            "tier": _user_tier(user),
            "is_new": is_new,
        }


async def soft_delete(user_id: int) -> bool:
    """soft delete + 30일 후 hard delete 큐.

    탈퇴 즉시:
      - is_active=False
      - deleted_at=now
    30일 후 별도 cron 이 hard delete (개인정보 파기 의무).
    """
    _db_required()
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import User

    session: AsyncSession
    async with _session_factory()() as session:
        user = await session.get(User, user_id)
        if user is None:
            return False
        user.is_active = False
        user.deleted_at = datetime.now(UTC)
        await session.commit()
        return True


async def get_active_user(user_id: int) -> dict[str, Any] | None:
    """활성 사용자 조회 — `get_current_user_id` dependency 가 호출."""
    _db_required()
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import User

    session: AsyncSession
    async with _session_factory()() as session:
        user = await session.get(User, user_id)
        if user is None or not user.is_active or user.deleted_at:
            return None
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "tier": await _resolve_active_tier(session, user.id),
        }


# 티어 등급 — 동시에 여러 활성 구독이 있으면 최고 등급을 채택.
_TIER_RANK: dict[str, int] = {"basic": 1, "standard": 2, "premium": 3, "family": 4}


async def _resolve_active_tier(session, user_id: int) -> str:  # noqa: ANN001
    """활성 구독(status=ACTIVE 이고 기간 만료 전) 중 최고 티어를 반환. 없으면 'anon'.

    이 값이 JWT 의 tier 클레임으로 발급되어 rate_limit·모델 분기의 단일 출처가 된다.
    구독 결제·해지 직후에는 클라이언트가 /auth/refresh 로 토큰을 갱신해야 즉시 반영된다.
    """
    from sqlalchemy import select

    from src.models.db_models import Subscription, SubscriptionStatus

    now = datetime.now(UTC)
    plans = (
        await session.execute(
            select(Subscription.plan).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.current_period_end > now,
            )
        )
    ).scalars().all()
    best = max(plans, key=lambda p: _TIER_RANK.get(p, 0), default=None)
    return best if best in _TIER_RANK else "anon"

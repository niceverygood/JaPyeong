"""user_service — DB 미설정 분기 + 입력 검증.

실제 DB 연결 분기는 통합 테스트(별도). 여기서는 단위 검증만:
  - DATABASE_URL 없으면 raise
  - signup 입력 부족 시 raise
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.services.user_service import (
    UserServiceError,
    get_active_user,
    login_with_oauth,
    login_with_password,
    signup,
    soft_delete,
)


async def test_signup_requires_database() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(UserServiceError, match="DATABASE_URL"):
            await signup(email="x@y.com", password="abc12345")


async def test_login_requires_database() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(UserServiceError, match="DATABASE_URL"):
            await login_with_password("x@y.com", "abc")


async def test_oauth_requires_database() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(UserServiceError, match="DATABASE_URL"):
            await login_with_oauth("kakao", "u-123")


async def test_soft_delete_requires_database() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(UserServiceError, match="DATABASE_URL"):
            await soft_delete(1)


async def test_get_active_user_requires_database() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(UserServiceError, match="DATABASE_URL"):
            await get_active_user(1)


async def test_signup_requires_password_or_oauth() -> None:
    """이메일만 + 비밀번호도 OAuth도 없으면 거부."""
    with patch.dict(os.environ, {"DATABASE_URL": "postgres://x"}, clear=False):
        with pytest.raises(UserServiceError, match="비밀번호 또는 OAuth"):
            await signup(email="x@y.com")

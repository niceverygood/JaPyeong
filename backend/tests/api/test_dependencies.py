"""api.dependencies — JWT/X-User-Id/관리자 권한 dependency 단위 테스트."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.api.dependencies import (
    get_admin_user_id,
    get_current_user_id,
    get_optional_user_id,
)
from src.security.jwt_auth import create_access_token

SECRET = "test-secret"


async def test_jwt_bearer_returns_user_id() -> None:
    with patch.dict(os.environ, {"JWT_SECRET": SECRET}, clear=False):
        token = create_access_token(user_id=99, secret=SECRET)
        with patch("src.security.jwt_auth.get_settings") as gs:
            gs.return_value.jwt_secret = SECRET
            gs.return_value.jwt_expire_days = 30
            result = await get_current_user_id(
                authorization=f"Bearer {token}",
                x_user_id=None,
            )
    assert result == 99


async def test_missing_token_raises_401() -> None:
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(authorization=None, x_user_id=None)
    assert exc.value.status_code == 401


async def test_invalid_token_raises_401() -> None:
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(
            authorization="Bearer not.a.valid.jwt",
            x_user_id=None,
        )
    assert exc.value.status_code == 401


async def test_x_user_id_fallback_disabled_by_default() -> None:
    """ALLOW_X_USER_ID=false → X-User-Id 헤더 무시, 401."""
    with patch.dict(os.environ, {}, clear=True), pytest.raises(HTTPException):
        await get_current_user_id(authorization=None, x_user_id="42")


async def test_x_user_id_fallback_when_enabled() -> None:
    with patch.dict(os.environ, {"ALLOW_X_USER_ID": "true"}, clear=False):
        result = await get_current_user_id(authorization=None, x_user_id="42")
    assert result == 42


async def test_x_user_id_invalid_int() -> None:
    with patch.dict(os.environ, {"ALLOW_X_USER_ID": "true"}, clear=False):
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(authorization=None, x_user_id="abc")
    assert exc.value.status_code == 400


async def test_optional_user_id_returns_none_on_missing() -> None:
    result = await get_optional_user_id(authorization=None, x_user_id=None)
    assert result is None


async def test_admin_token_required() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(HTTPException) as exc:
            await get_admin_user_id(authorization="Bearer any")
    assert exc.value.status_code == 503


async def test_admin_token_correct() -> None:
    with patch.dict(os.environ, {"ADMIN_BEARER_TOKEN": "secret-admin-key"}, clear=False):
        result = await get_admin_user_id(authorization="Bearer secret-admin-key")
    assert result == 0


async def test_admin_token_wrong() -> None:
    with patch.dict(os.environ, {"ADMIN_BEARER_TOKEN": "secret-admin-key"}, clear=False):
        with pytest.raises(HTTPException) as exc:
            await get_admin_user_id(authorization="Bearer wrong-key")
    assert exc.value.status_code == 403

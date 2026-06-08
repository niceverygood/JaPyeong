"""config — production secret 가드 단위 테스트."""

from __future__ import annotations

import pytest

from src.core.config import Settings, _validate_production_secrets


def test_local_env_skips_validation() -> None:
    """local 환경은 default 허용 (개발 편의)."""
    s = Settings(env="local", jwt_secret="change-me-in-production")
    _validate_production_secrets(s)  # no raise


def test_production_rejects_default_jwt_secret() -> None:
    s = Settings(env="production", jwt_secret="change-me-in-production")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        _validate_production_secrets(s)


def test_production_rejects_short_jwt_secret() -> None:
    s = Settings(env="production", jwt_secret="short")
    with pytest.raises(RuntimeError, match="너무 짧"):
        _validate_production_secrets(s)


def test_production_rejects_oauth_placeholder_enabled() -> None:
    s = Settings(
        env="production",
        jwt_secret="a" * 48,
        oauth_placeholder_enabled=True,
    )
    with pytest.raises(RuntimeError, match="OAUTH_PLACEHOLDER"):
        _validate_production_secrets(s)


def test_production_passes_with_strong_secret_and_disabled_oauth() -> None:
    s = Settings(
        env="production",
        jwt_secret="a" * 48,
        oauth_placeholder_enabled=False,
    )
    _validate_production_secrets(s)  # no raise


def test_staging_also_enforces_guards() -> None:
    """non-local 환경은 동일하게 가드."""
    s = Settings(env="staging", jwt_secret="change-me-in-production")
    with pytest.raises(RuntimeError):
        _validate_production_secrets(s)

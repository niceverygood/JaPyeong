"""JWT 발급/검증 + bcrypt 단위 테스트."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from src.security.jwt_auth import (
    ALGORITHM,
    ISSUER,
    AuthError,
    create_access_token,
    decode_token,
    extract_bearer,
    hash_password,
    verify_password,
)

SECRET = "test-secret-do-not-use-in-prod"


# ── bcrypt ────────────────────────────────────────────
def test_hash_password_roundtrip() -> None:
    h = hash_password("mySecret123!")
    assert h != "mySecret123!"
    assert verify_password("mySecret123!", h)
    assert not verify_password("wrong", h)


def test_hash_password_different_salts() -> None:
    """같은 비밀번호도 다른 salt → 다른 해시."""
    h1 = hash_password("samepw")
    h2 = hash_password("samepw")
    assert h1 != h2
    assert verify_password("samepw", h1)
    assert verify_password("samepw", h2)


def test_empty_password_rejected() -> None:
    with pytest.raises(ValueError):
        hash_password("")


def test_password_too_long() -> None:
    with pytest.raises(ValueError):
        hash_password("x" * 100)


def test_verify_handles_invalid_hash() -> None:
    """잘못된 해시 형식 → False (예외 X)."""
    assert not verify_password("any", "")
    assert not verify_password("any", "not-a-bcrypt-hash")
    assert not verify_password("", "$2b$12$valid")


# ── JWT ───────────────────────────────────────────────
def test_create_and_decode_token() -> None:
    token = create_access_token(user_id=42, tier="premium", secret=SECRET)
    claims = decode_token(token, secret=SECRET)
    assert claims.user_id == 42
    assert claims.tier == "premium"
    assert claims.expires_at > claims.issued_at


def test_decode_with_wrong_secret() -> None:
    token = create_access_token(user_id=1, secret=SECRET)
    with pytest.raises(AuthError):
        decode_token(token, secret="other-secret")


def test_decode_expired_token() -> None:
    """만료된 토큰 거부."""
    token = create_access_token(user_id=1, expires_in_days=-1, secret=SECRET)
    with pytest.raises(AuthError):
        decode_token(token, secret=SECRET)


def test_decode_empty_token() -> None:
    with pytest.raises(AuthError):
        decode_token("", secret=SECRET)


def test_decode_malformed_token() -> None:
    with pytest.raises(AuthError):
        decode_token("not.a.jwt", secret=SECRET)


def test_decode_token_without_required_claims() -> None:
    """sub/exp/iat 누락 → AuthError."""
    bad = jwt.encode({"iss": ISSUER}, SECRET, algorithm=ALGORITHM)
    with pytest.raises(AuthError):
        decode_token(bad, secret=SECRET)


def test_decode_token_wrong_issuer() -> None:
    """iss 가 japyeong 아니면 거부."""
    now = datetime.now(UTC)
    bad = jwt.encode(
        {
            "sub": "1",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=1)).timestamp()),
            "iss": "other-app",
        },
        SECRET,
        algorithm=ALGORITHM,
    )
    with pytest.raises(AuthError):
        decode_token(bad, secret=SECRET)


def test_decode_token_non_integer_sub() -> None:
    now = datetime.now(UTC)
    bad = jwt.encode(
        {
            "sub": "not-an-int",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=1)).timestamp()),
            "iss": ISSUER,
        },
        SECRET,
        algorithm=ALGORITHM,
    )
    with pytest.raises(AuthError):
        decode_token(bad, secret=SECRET)


def test_token_iat_within_one_second() -> None:
    """iat 이 발급 시각과 거의 같다."""
    before = int(time.time())
    token = create_access_token(user_id=1, secret=SECRET)
    after = int(time.time())
    claims = decode_token(token, secret=SECRET)
    assert before - 1 <= int(claims.issued_at.timestamp()) <= after + 1


# ── extract_bearer ────────────────────────────────────
def test_extract_bearer_valid() -> None:
    assert extract_bearer("Bearer abc123") == "abc123"
    assert extract_bearer("bearer abc123") == "abc123"  # case-insensitive
    assert extract_bearer("BEARER xyz") == "xyz"


def test_extract_bearer_invalid() -> None:
    assert extract_bearer(None) is None
    assert extract_bearer("") is None
    assert extract_bearer("abc") is None  # no scheme
    assert extract_bearer("Basic abc") is None  # wrong scheme
    assert extract_bearer("Bearer ") is None  # empty token

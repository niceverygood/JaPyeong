"""JWT 발급/검증 + 비밀번호 해시 — 회원 인증 토대.

토큰:
  - access_token: 30일 (config.jwt_expire_days)
  - HS256, settings.jwt_secret
  - payload: {sub: user_id, tier: str, exp: int, iat: int, iss: "japyeong"}

비밀번호:
  - bcrypt cost=12 (사용자 등록·로그인 시)
  - 평문 저장 절대 금지
  - 환경: WORK_FACTOR_BCRYPT (default 12)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from src.core.config import get_settings

ISSUER = "japyeong"
ALGORITHM = "HS256"


class AuthError(Exception):
    """JWT 검증 실패 / 만료 / 형식 오류."""


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """JWT payload 디코드 결과."""

    user_id: int
    tier: str          # anon / basic / standard / premium / family
    issued_at: datetime
    expires_at: datetime


# ── 비밀번호 해시 ──────────────────────────────────────
def _bcrypt_rounds() -> int:
    return int(os.environ.get("WORK_FACTOR_BCRYPT", "12"))


def hash_password(plaintext: str) -> str:
    """평문 비밀번호 → bcrypt 해시 (DB 저장용)."""
    if not plaintext:
        raise ValueError("비밀번호는 빈 문자열일 수 없습니다.")
    if len(plaintext) > 72:
        # bcrypt 입력 길이 제한 (72바이트). 그 이상은 자르거나 raise.
        raise ValueError("비밀번호는 72자 이하여야 합니다.")
    salt = bcrypt.gensalt(rounds=_bcrypt_rounds())
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """비밀번호 검증 — 타이밍 안전."""
    if not plaintext or not hashed:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ── JWT 발급 / 검증 ────────────────────────────────────
def create_access_token(
    user_id: int,
    tier: str = "anon",
    expires_in_days: int | None = None,
    secret: str | None = None,
) -> str:
    """JWT access token 발급."""
    settings = get_settings()
    days = expires_in_days if expires_in_days is not None else settings.jwt_expire_days
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tier": tier,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=days)).timestamp()),
        "iss": ISSUER,
    }
    return jwt.encode(payload, secret or settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str | None = None) -> TokenClaims:
    """JWT 디코드 + 검증.

    Raises:
        AuthError: 만료 / 서명 불일치 / 형식 오류
    """
    if not token:
        raise AuthError("빈 토큰")
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            secret or settings.jwt_secret,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"require": ["sub", "exp", "iat"]},
        )
    except JWTError as e:
        raise AuthError(f"토큰 검증 실패: {e}") from e

    try:
        user_id = int(payload["sub"])
    except (ValueError, KeyError) as e:
        raise AuthError(f"sub 클레임 형식 오류: {e}") from e

    return TokenClaims(
        user_id=user_id,
        tier=payload.get("tier", "anon"),
        issued_at=datetime.fromtimestamp(payload["iat"], tz=UTC),
        expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
    )


def extract_bearer(authorization: str | None) -> str | None:
    """Authorization 헤더에서 Bearer 토큰만 추출."""
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None

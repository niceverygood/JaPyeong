"""FastAPI 공통 dependency — JWT 디코드 + user_id 추출.

사용:
  @router.get("/me")
  async def me(user_id: int = Depends(get_current_user_id)):
      ...

  @router.get("/admin/x")
  async def admin(user_id: int = Depends(get_admin_user_id)):
      ...

JWT 미설정 / 만료 / 위조 → 401.
관리자 권한 부재 → 403.

레거시 호환:
  X-User-Id 헤더 (정수) — DEV 환경 또는 마이그레이션 기간만 허용.
  설정 ALLOW_X_USER_ID=true 일 때만 fallback.
"""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Header, HTTPException, status

from src.security.jwt_auth import AuthError, decode_token, extract_bearer


def _allow_x_user_id_fallback() -> bool:
    # 프로덕션에서는 절대 허용 안 함 — X-User-Id 신원 위조(임퍼소네이션) 차단.
    if os.environ.get("ENV", "").strip().lower() == "production":
        return False
    return os.environ.get("ALLOW_X_USER_ID", "false").lower() in ("1", "true", "yes")


def _map_auth_error(e: AuthError) -> str:
    """jose 라이브러리 영문 메시지를 사용자용 한국어로 매핑.

    구체 원인을 클라이언트에 누출하지 않음.
    """
    msg = str(e).lower()
    if "expired" in msg or "만료" in msg:
        return "세션이 만료되었습니다. 다시 로그인해주세요."
    return "인증에 실패했습니다. 다시 로그인해주세요."


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> int:
    """JWT bearer → user_id (또는 dev 환경의 X-User-Id 헤더)."""
    token = extract_bearer(authorization)
    if token:
        try:
            claims = decode_token(token)
            return claims.user_id
        except AuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_map_auth_error(e),
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    # Fallback for dev only
    if _allow_x_user_id_fallback() and x_user_id:
        try:
            return int(x_user_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-User-Id must be integer",
            ) from e

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 토큰이 필요합니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user_id(
    authorization: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> int | None:
    """비로그인 허용 엔드포인트용 — 없으면 None."""
    try:
        return await get_current_user_id(authorization, x_user_id)
    except HTTPException:
        return None


def _admin_token() -> str | None:
    return os.environ.get("ADMIN_BEARER_TOKEN")


async def get_admin_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> int:
    """관리자 전용 엔드포인트.

    ADMIN_BEARER_TOKEN 환경변수와 일치하는 정적 bearer를 요구.
    user_id 는 0 (system) 반환.
    """
    expected = _admin_token()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="관리자 토큰 미설정",
        )
    token = extract_bearer(authorization)
    # 상수 시간 비교 (timing attack 방지)
    import hmac
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한 필요",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return 0

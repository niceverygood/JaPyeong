"""회원 가입·로그인·탈퇴 라우터.

엔드포인트:
  POST /api/v1/auth/signup       이메일+비밀번호 가입
  POST /api/v1/auth/login        이메일+비밀번호 로그인
  POST /api/v1/auth/oauth        카카오/애플/구글 (provider+subject)
  POST /api/v1/auth/refresh      JWT 재발급 (현재 토큰 검증 후 새 토큰)
  DELETE /api/v1/auth/me         회원 탈퇴 (soft delete)
  GET /api/v1/auth/me            현재 회원 정보
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from src.api.dependencies import get_current_user_id
from src.core.config import get_settings
from src.security.jwt_auth import create_access_token
from src.services.user_service import (
    DatabaseUnavailableError,
    UserServiceError,
    get_active_user,
    login_with_oauth,
    login_with_password,
    signup,
    soft_delete,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request/Response 스키마 ─────────────────────────────
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str | None = Field(default=None, max_length=40)
    phone: str | None = Field(default=None, max_length=40)
    marketing_consent: bool = False


class LoginRequest(BaseModel):
    # 로그인 측은 min_length=1 — legacy 8자 미만 비번 계정 호환
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class OAuthRequest(BaseModel):
    provider: Literal["kakao", "apple", "google"]
    subject: str = Field(min_length=1, max_length=128)
    email: EmailStr | None = None
    name: str | None = Field(default=None, max_length=40)


class AuthResponse(BaseModel):
    user_id: int
    token: str
    tier: str
    is_new: bool = False


class MeResponse(BaseModel):
    user_id: int
    email: str | None
    name: str | None
    tier: str


# ── 엔드포인트 ──────────────────────────────────────────
@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup_endpoint(body: SignupRequest) -> AuthResponse:
    try:
        result = await signup(
            email=body.email,
            password=body.password,
            name=body.name,
            phone=body.phone,
            marketing_consent=body.marketing_consent,
        )
    except DatabaseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail="일시적으로 가입할 수 없습니다. 잠시 후 다시 시도해주세요.",
        ) from e
    except UserServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return AuthResponse(**result, is_new=True)


@router.post("/login", response_model=AuthResponse)
async def login_endpoint(body: LoginRequest) -> AuthResponse:
    try:
        result = await login_with_password(body.email, body.password)
    except DatabaseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail="일시적으로 로그인할 수 없습니다. 잠시 후 다시 시도해주세요.",
        ) from e
    except UserServiceError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    return AuthResponse(**result, is_new=False)


@router.post("/oauth", response_model=AuthResponse)
async def oauth_endpoint(body: OAuthRequest) -> AuthResponse:
    # placeholder OAuth — provider 토큰 검증 미구현. 프로덕션 차단.
    if not get_settings().oauth_placeholder_enabled:
        raise HTTPException(
            status_code=503,
            detail="OAuth 로그인은 곧 제공됩니다.",
        )
    try:
        result = await login_with_oauth(
            oauth_provider=body.provider,
            oauth_subject=body.subject,
            email=body.email,
            name=body.name,
        )
    except DatabaseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail="일시적으로 로그인할 수 없습니다. 잠시 후 다시 시도해주세요.",
        ) from e
    except UserServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return AuthResponse(**result)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_endpoint(
    user_id: int = Depends(get_current_user_id),
) -> AuthResponse:
    """현재 토큰 유효 → 새 토큰 발급 (만료된 토큰은 거부됨)."""
    user = await get_active_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="회원이 활성 상태가 아닙니다.")
    token = create_access_token(user_id, tier=user["tier"])
    return AuthResponse(
        user_id=user_id,
        token=token,
        tier=user["tier"],
        is_new=False,
    )


@router.get("/me", response_model=MeResponse)
async def me_endpoint(user_id: int = Depends(get_current_user_id)) -> MeResponse:
    user = await get_active_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
    return MeResponse(**user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me_endpoint(
    user_id: int = Depends(get_current_user_id),
) -> None:
    """회원 탈퇴 — soft delete.

    개인정보보호법: 동의 철회 시 30일 내 파기.
    별도 cron 이 30일 경과한 soft-deleted 사용자 hard delete.
    """
    ok = await soft_delete(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

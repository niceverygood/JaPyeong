"""/v1/notifications 라우터 — 푸시 토큰 등록 + 알림 설정.

자평 가드:
  - 토큰 등록은 사용자 명시적 액션 (모바일 useDailyFortunePush 훅)
  - prefs 변경은 즉시 반영
  - DATABASE_URL 미설정 시 dummy success (현재 운영 안전)

Sprint 1-2 회원 도입 후:
  - JWT 헤더에서 user_id 자동 추출
  - 현재는 X-User-Id 헤더 (회원 도입 전 임시)
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


# ── DTO ──────────────────────────────────────────────────
class RegisterTokenRequest(BaseModel):
    expo_push_token: str = Field(min_length=1, max_length=256)
    platform: str = Field(pattern=r"^(ios|android|web)$")


class RegisterTokenResponse(BaseModel):
    ok: bool
    token_id: int | None = None


class NotificationPrefRequest(BaseModel):
    daily_fortune_enabled: bool
    daily_fortune_time_hhmm: str | None = Field(
        default=None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$",
    )
    negative_fortune_muted: bool | None = None


class NotificationPrefResponse(BaseModel):
    ok: bool


# ── 헬퍼: DB 활성 여부 ──────────────────────────────────
def _db_enabled() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


def _get_user_id(x_user_id: str | None) -> int | None:
    """X-User-Id 헤더에서 정수 user_id 추출.

    Sprint 1-2 후엔 JWT 디코드로 대체.
    """
    if not x_user_id:
        return None
    try:
        return int(x_user_id)
    except ValueError:
        return None


# ── POST /register-token ──────────────────────────────────
@router.post("/register-token", response_model=RegisterTokenResponse)
async def register_token(
    req: RegisterTokenRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> RegisterTokenResponse:
    """모바일 앱에서 발급받은 Expo Push 토큰을 백엔드에 저장."""
    user_id = _get_user_id(x_user_id)

    # DB 비활성 또는 비회원 → silent success (모바일은 토큰 발급은 성공)
    if not _db_enabled():
        return RegisterTokenResponse(ok=True, token_id=None)
    if user_id is None:
        return RegisterTokenResponse(ok=True, token_id=None)

    # 지연 import (DB 미설정 환경에서 sqlalchemy import 비용 회피)
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import PushToken

    session: AsyncSession
    async with _session_factory()() as session:
        # 이미 등록된 토큰이면 last_used_at 만 갱신 (upsert)
        stmt = select(PushToken).where(
            PushToken.user_id == user_id,
            PushToken.token == req.expo_push_token,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.is_active = True
            existing.last_used_at = datetime.now(UTC)
            existing.last_error = None
            await session.commit()
            await session.refresh(existing)
            return RegisterTokenResponse(ok=True, token_id=existing.id)

        # 신규 토큰
        row = PushToken(
            user_id=user_id,
            token=req.expo_push_token,
            platform=req.platform,
            is_active=True,
            last_used_at=datetime.now(UTC),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return RegisterTokenResponse(ok=True, token_id=row.id)


# ── POST /preferences ────────────────────────────────────
@router.post("/preferences", response_model=NotificationPrefResponse)
async def update_preferences(
    req: NotificationPrefRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> NotificationPrefResponse:
    """알림 수신 설정 변경 — opt-in / opt-out + 시간 + 부정 통변 끄기."""
    user_id = _get_user_id(x_user_id)

    if not _db_enabled() or user_id is None:
        # 로컬에만 저장하는 환경 — silent success
        return NotificationPrefResponse(ok=True)

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import User

    session: AsyncSession
    async with _session_factory()() as session:
        user = await session.get(User, user_id)
        if user is None:
            raise HTTPException(404, "사용자를 찾을 수 없습니다.")

        user.notif_daily_enabled = req.daily_fortune_enabled
        if req.daily_fortune_time_hhmm:
            user.notif_daily_time_hhmm = req.daily_fortune_time_hhmm
        if req.negative_fortune_muted is not None:
            user.notif_negative_muted = req.negative_fortune_muted

        await session.commit()
        return NotificationPrefResponse(ok=True)

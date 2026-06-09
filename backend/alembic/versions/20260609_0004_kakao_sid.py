"""KakaoPay 정기결제 SID 컬럼 추가

Revision ID: 0004_kakao_sid
Revises: 0003_push_notifications
Create Date: 2026-06-09

카카오페이 정기결제(subscription):
  - subscription.kakao_sid 추가 — 정기 CID 로 첫 승인 시 발급되는 정기결제 키.
    2회차부터 사용자 인증 없이 자동청구(/v1/payment/subscription)에 사용한다.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_kakao_sid"
down_revision: str | None = "0003_push_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "subscription",
        sa.Column("kakao_sid", sa.String(128), nullable=True, unique=True),
    )


def downgrade() -> None:
    op.drop_column("subscription", "kakao_sid")

"""push notifications — push_token, notification_log, user notif prefs

Revision ID: 0003_push_notifications
Revises: 0002_bm_v2_schema
Create Date: 2026-06-07

BM v2 Sprint 3-4 첫 Retention hook 인프라:
  - user: notif_daily_enabled / notif_daily_time_hhmm / notif_negative_muted
  - push_token (Expo Push / FCM 토큰)
  - notification_log (발송 감사)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_push_notifications"
down_revision: str | None = "0002_bm_v2_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── User 일진 알림 prefs ─────────────────────────────────
    op.add_column(
        "user",
        sa.Column(
            "notif_daily_enabled", sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "notif_daily_time_hhmm", sa.String(5),
            nullable=False, server_default="08:00",
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "notif_negative_muted", sa.Boolean(),
            nullable=False, server_default=sa.false(),
        ),
    )

    # ── push_token ───────────────────────────────────────────
    op.create_table(
        "push_token",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("token", sa.String(256), nullable=False),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(),
            nullable=False, server_default=sa.true(),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.String(255)),
        sa.UniqueConstraint("user_id", "token", name="uq_push_token_user_token"),
    )
    op.create_index("ix_push_token_user_id", "push_token", ["user_id"])
    op.create_index("ix_push_token_token", "push_token", ["token"])

    # ── notification_log ─────────────────────────────────────
    op.create_table(
        "notification_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "push_token_id", sa.BigInteger(),
            sa.ForeignKey("push_token.id", ondelete="SET NULL"),
        ),
        sa.Column("notification_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("body", sa.String(500), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column(
            "provider_response", postgresql.JSONB(astext_type=sa.Text()),
        ),
        sa.Column(
            "sent_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_notification_log_user_id", "notification_log", ["user_id"])
    op.create_index("ix_notification_log_sent_at", "notification_log", ["sent_at"])


def downgrade() -> None:
    op.drop_index("ix_notification_log_sent_at", table_name="notification_log")
    op.drop_index("ix_notification_log_user_id", table_name="notification_log")
    op.drop_table("notification_log")

    op.drop_index("ix_push_token_token", table_name="push_token")
    op.drop_index("ix_push_token_user_id", table_name="push_token")
    op.drop_table("push_token")

    op.drop_column("user", "notif_negative_muted")
    op.drop_column("user", "notif_daily_time_hhmm")
    op.drop_column("user", "notif_daily_enabled")

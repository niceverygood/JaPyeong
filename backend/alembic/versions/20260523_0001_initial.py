"""initial schema — user/birth_record/conversation/message/subscription/preorder/validation_case

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-23
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("oauth_provider", sa.String(40)),
        sa.Column("oauth_subject", sa.String(255)),
        sa.Column("name", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("oauth_provider", "oauth_subject", name="uq_user_oauth"),
    )
    op.create_index("ix_user_email", "user", ["email"])

    op.create_table(
        "birth_record",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(80)),
        sa.Column("encrypted_payload", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_birth_record_user_id", "birth_record", ["user_id"])

    op.create_table(
        "conversation",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("birth_record_id", sa.BigInteger(), sa.ForeignKey("birth_record.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_conversation_user_id", "conversation", ["user_id"])
    op.create_index("ix_conversation_birth_record_id", "conversation", ["birth_record_id"])

    op.create_table(
        "message",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("basis", sa.Text()),
        sa.Column("citations", postgresql.JSONB()),
        sa.Column("flags", postgresql.JSONB()),
        sa.Column("model", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_message_conversation_id", "message", ["conversation_id"])
    op.create_index("ix_message_created_at", "message", ["created_at"])

    op.create_table(
        "subscription",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("portone_subscription_id", sa.String(128), unique=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("canceled_at", sa.DateTime(timezone=True)),
        sa.Column("price_krw", sa.Integer(), nullable=False),
    )
    op.create_index("ix_subscription_user_id", "subscription", ["user_id"])

    op.create_table(
        "preorder",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(80)),
        sa.Column("plan", sa.String(32), nullable=False, server_default="undecided"),
        sa.Column("source", sa.String(40)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_preorder_email", "preorder", ["email"])

    op.create_table(
        "validation_case",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("case_id", sa.String(80), nullable=False, unique=True),
        sa.Column("source", sa.String(240), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("approved_by", sa.String(80)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("accuracy_score", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("validation_case")
    op.drop_index("ix_preorder_email", table_name="preorder")
    op.drop_table("preorder")
    op.drop_index("ix_subscription_user_id", table_name="subscription")
    op.drop_table("subscription")
    op.drop_index("ix_message_created_at", table_name="message")
    op.drop_index("ix_message_conversation_id", table_name="message")
    op.drop_table("message")
    op.drop_index("ix_conversation_birth_record_id", table_name="conversation")
    op.drop_index("ix_conversation_user_id", table_name="conversation")
    op.drop_table("conversation")
    op.drop_index("ix_birth_record_user_id", table_name="birth_record")
    op.drop_table("birth_record")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")

"""코인 경제 — 선충전 지갑 + 원장 (ARPU 엔진)

Revision ID: 0005_coin_economy
Revises: 0004_kakao_sid
Create Date: 2026-06-14

테이블:
  - coin_wallet      : 사용자별 코인 잔액(원장 합과 일치 유지)
  - coin_transaction : 모든 적립/차감 1건 1행 (감사·정합성, 멱등 unique)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_coin_economy"
down_revision: str | None = "0004_kakao_sid"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "coin_wallet",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_charged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_spent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_coin_wallet_user"),
    )
    op.create_index("ix_coin_wallet_user_id", "coin_wallet", ["user_id"])

    op.create_table(
        "coin_transaction",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "wallet_id",
            sa.BigInteger(),
            sa.ForeignKey("coin_wallet.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(40), nullable=True),
        sa.Column(
            "payment_id",
            sa.BigInteger(),
            sa.ForeignKey("payment.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("idempotency_key", sa.String(160), nullable=True),
        sa.Column("memo", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("idempotency_key", name="uq_coin_txn_idem"),
    )
    op.create_index("ix_coin_transaction_wallet_id", "coin_transaction", ["wallet_id"])
    op.create_index("ix_coin_transaction_user_id", "coin_transaction", ["user_id"])
    op.create_index("ix_coin_transaction_created_at", "coin_transaction", ["created_at"])


def downgrade() -> None:
    op.drop_table("coin_transaction")
    op.drop_table("coin_wallet")

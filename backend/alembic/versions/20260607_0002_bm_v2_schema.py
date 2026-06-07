"""BM v2 schema upgrade — 4티어 + 자문위원 + 결정 추적 + Family + Payment + Refunds

Revision ID: 0002_bm_v2_schema
Revises: 0001_initial
Create Date: 2026-06-07

BM v2 핵심 데이터 모델:
  ❶ 결정 추적 데이터셋 (decision_log) — 진짜 해자 ❶
  ❷ 자문위원 풀 (advisor + advisor_session) — 진짜 해자 ❷
  ❸ Family 패키지 (family_member + 14세+ 동의 게이트)
  ❹ Payment + RefundRequest — 단계별 청약철회 회수율
  ❺ Subscription 4티어 + 자동갱신 opt-in + 채널 어트리뷰션
  ❻ RateLimitEvent 감사·모니터링

기존 테이블 변경:
  - user: phone, deleted_at, marketing_consent 추가
  - subscription: channel, tm_partner_code, autorenew*, renewal_notice_*,
                  portone_billing_key, expired_at 추가; portone_subscription_id 제거
  - message: tone_audit 추가
  - subscription.plan enum: standard/premium/pro → basic/standard/premium/family/pro
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_bm_v2_schema"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── User 컬럼 추가 ───────────────────────────────────────
    op.add_column("user", sa.Column("phone", sa.String(40), nullable=True))
    op.add_column("user", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "user",
        sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user",
        sa.Column("marketing_consent_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Subscription 컬럼 재구성 ─────────────────────────────
    op.add_column(
        "subscription",
        sa.Column("channel", sa.String(32), nullable=False, server_default="self_serve"),
    )
    op.add_column(
        "subscription",
        sa.Column("tm_partner_code", sa.String(40), nullable=True),
    )
    op.create_index(
        "ix_subscription_tm_partner_code", "subscription", ["tm_partner_code"],
    )
    op.create_index("ix_subscription_status", "subscription", ["status"])
    op.create_index(
        "ix_subscription_current_period_end", "subscription", ["current_period_end"],
    )
    op.add_column(
        "subscription",
        sa.Column("autorenew", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "subscription",
        sa.Column("autorenew_optin_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "subscription",
        sa.Column("renewal_notice_30d_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "subscription",
        sa.Column("renewal_notice_7d_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "subscription",
        sa.Column("renewal_notice_1d_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "subscription",
        sa.Column("portone_billing_key", sa.String(128), nullable=True, unique=True),
    )
    op.add_column(
        "subscription",
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
    )
    # 0001 의 portone_subscription_id 는 billing_key 로 대체 → 제거
    op.drop_column("subscription", "portone_subscription_id")

    # ── Message: tone_audit 추가 ─────────────────────────────
    op.add_column(
        "message",
        sa.Column("tone_audit", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # ── Payment 신규 ──────────────────────────────────────────
    op.create_table(
        "payment",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "subscription_id", sa.BigInteger(),
            sa.ForeignKey("subscription.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("amount_krw", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_tx_id", sa.String(128), unique=True),
        sa.Column("method", sa.String(40)),
        sa.Column("receipt_url", sa.String(500)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("refunded_at", sa.DateTime(timezone=True)),
        sa.Column("refund_amount_krw", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_payment_subscription_id", "payment", ["subscription_id"])
    op.create_index("ix_payment_user_id", "payment", ["user_id"])
    op.create_index("ix_payment_status", "payment", ["status"])
    op.create_index("ix_payment_created_at", "payment", ["created_at"])
    op.create_index("ix_payment_provider_tx_id", "payment", ["provider_tx_id"])

    # ── RefundRequest 신규 ────────────────────────────────────
    op.create_table(
        "refund_request",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "payment_id", sa.BigInteger(),
            sa.ForeignKey("payment.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "requested_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(),
        ),
        sa.Column("days_since_payment", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("refund_amount_krw", sa.Integer(), nullable=False),
        sa.Column(
            "tm_commission_clawback_krw", sa.Integer(), nullable=False, server_default="0",
        ),
        sa.Column("reason", sa.String(500)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("processed_by", sa.String(80)),
    )
    op.create_index("ix_refund_request_payment_id", "refund_request", ["payment_id"])
    op.create_index("ix_refund_request_user_id", "refund_request", ["user_id"])

    # ── Advisor 신규 ──────────────────────────────────────────
    op.create_table(
        "advisor",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(40)),
        sa.Column("bio", sa.Text()),
        sa.Column("years_experience", sa.Integer()),
        sa.Column("publications", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("media_appearances", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("contract_started_at", sa.DateTime(timezone=True)),
        sa.Column("contract_ends_at", sa.DateTime(timezone=True)),
        sa.Column("is_exclusive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rate_per_session_krw", sa.Integer()),
        sa.Column("weekly_hours_max", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("grade", sa.String(16)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
        ),
    )

    # ── AdvisorSession 신규 ───────────────────────────────────
    op.create_table(
        "advisor_session",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "advisor_id", sa.BigInteger(),
            sa.ForeignKey("advisor.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column(
            "subscription_id", sa.BigInteger(),
            sa.ForeignKey("subscription.id", ondelete="SET NULL"),
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("recording_consent_at", sa.DateTime(timezone=True)),
        sa.Column("recording_url", sa.String(500)),
        sa.Column("notes_encrypted", sa.LargeBinary()),
        sa.Column("satisfaction_score", sa.Integer()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_advisor_session_user_id", "advisor_session", ["user_id"])
    op.create_index("ix_advisor_session_advisor_id", "advisor_session", ["advisor_id"])

    # ── DecisionLog 신규 (진짜 해자 ❶) ───────────────────────
    op.create_table(
        "decision_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "birth_record_id", sa.BigInteger(),
            sa.ForeignKey("birth_record.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("decision_type", sa.String(40), nullable=False),
        sa.Column("sajupillars_anon", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("option_a_summary", sa.Text()),
        sa.Column("option_b_summary", sa.Text()),
        sa.Column("user_context", sa.Text()),
        sa.Column("lean", sa.String(16)),
        sa.Column("advisor_response_summary", sa.Text()),
        sa.Column("confidence", sa.String(16)),
        sa.Column("actual_choice", sa.String(16)),
        sa.Column("actual_choice_at", sa.DateTime(timezone=True)),
        sa.Column("followup_3m_due_at", sa.DateTime(timezone=True)),
        sa.Column("followup_3m_sent_at", sa.DateTime(timezone=True)),
        sa.Column("followup_3m_satisfaction", sa.Integer()),
        sa.Column("followup_6m_due_at", sa.DateTime(timezone=True)),
        sa.Column("followup_6m_sent_at", sa.DateTime(timezone=True)),
        sa.Column("followup_6m_satisfaction", sa.Integer()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_decision_log_user_id", "decision_log", ["user_id"])
    op.create_index("ix_decision_log_birth_record_id", "decision_log", ["birth_record_id"])
    op.create_index("ix_decision_log_decision_type", "decision_log", ["decision_type"])
    op.create_index("ix_decision_log_created_at", "decision_log", ["created_at"])
    op.create_index("ix_decision_log_followup_3m_due", "decision_log", ["followup_3m_due_at"])
    op.create_index("ix_decision_log_followup_6m_due", "decision_log", ["followup_6m_due_at"])

    # ── FamilyMember 신규 (BM v2 Family 패키지) ──────────────
    op.create_table(
        "family_member",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "birth_record_id", sa.BigInteger(),
            sa.ForeignKey("birth_record.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("relation", sa.String(32), nullable=False),
        sa.Column("is_minor", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_status", sa.String(32), nullable=False, server_default="not_required"),
        sa.Column("consent_requested_at", sa.DateTime(timezone=True)),
        sa.Column("consent_granted_at", sa.DateTime(timezone=True)),
        sa.Column("consent_contact", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_family_member_user_id", "family_member", ["user_id"])
    op.create_index("ix_family_member_birth_record_id", "family_member", ["birth_record_id"])

    # ── RateLimitEvent 신규 (감사·모니터링) ───────────────────
    op.create_table(
        "rate_limit_event",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ip", sa.String(64), nullable=False),
        sa.Column(
            "user_id", sa.BigInteger(),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
        ),
        sa.Column("user_tier", sa.String(32)),
        sa.Column("layer", sa.String(40), nullable=False),
        sa.Column("limit_value", sa.Integer(), nullable=False),
        sa.Column("actual_count", sa.Integer(), nullable=False),
        sa.Column("user_agent", sa.String(500)),
        sa.Column(
            "blocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rate_limit_event_ip", "rate_limit_event", ["ip"])
    op.create_index("ix_rate_limit_event_blocked_at", "rate_limit_event", ["blocked_at"])


def downgrade() -> None:
    op.drop_index("ix_rate_limit_event_blocked_at", table_name="rate_limit_event")
    op.drop_index("ix_rate_limit_event_ip", table_name="rate_limit_event")
    op.drop_table("rate_limit_event")

    op.drop_index("ix_family_member_birth_record_id", table_name="family_member")
    op.drop_index("ix_family_member_user_id", table_name="family_member")
    op.drop_table("family_member")

    op.drop_index("ix_decision_log_followup_6m_due", table_name="decision_log")
    op.drop_index("ix_decision_log_followup_3m_due", table_name="decision_log")
    op.drop_index("ix_decision_log_created_at", table_name="decision_log")
    op.drop_index("ix_decision_log_decision_type", table_name="decision_log")
    op.drop_index("ix_decision_log_birth_record_id", table_name="decision_log")
    op.drop_index("ix_decision_log_user_id", table_name="decision_log")
    op.drop_table("decision_log")

    op.drop_index("ix_advisor_session_advisor_id", table_name="advisor_session")
    op.drop_index("ix_advisor_session_user_id", table_name="advisor_session")
    op.drop_table("advisor_session")

    op.drop_table("advisor")

    op.drop_index("ix_refund_request_user_id", table_name="refund_request")
    op.drop_index("ix_refund_request_payment_id", table_name="refund_request")
    op.drop_table("refund_request")

    op.drop_index("ix_payment_provider_tx_id", table_name="payment")
    op.drop_index("ix_payment_created_at", table_name="payment")
    op.drop_index("ix_payment_status", table_name="payment")
    op.drop_index("ix_payment_user_id", table_name="payment")
    op.drop_index("ix_payment_subscription_id", table_name="payment")
    op.drop_table("payment")

    op.drop_column("message", "tone_audit")

    op.add_column(
        "subscription",
        sa.Column("portone_subscription_id", sa.String(128), nullable=True, unique=True),
    )
    op.drop_column("subscription", "expired_at")
    op.drop_column("subscription", "portone_billing_key")
    op.drop_column("subscription", "renewal_notice_1d_sent_at")
    op.drop_column("subscription", "renewal_notice_7d_sent_at")
    op.drop_column("subscription", "renewal_notice_30d_sent_at")
    op.drop_column("subscription", "autorenew_optin_at")
    op.drop_column("subscription", "autorenew")
    op.drop_index("ix_subscription_current_period_end", table_name="subscription")
    op.drop_index("ix_subscription_status", table_name="subscription")
    op.drop_index("ix_subscription_tm_partner_code", table_name="subscription")
    op.drop_column("subscription", "tm_partner_code")
    op.drop_column("subscription", "channel")

    op.drop_column("user", "marketing_consent_at")
    op.drop_column("user", "marketing_consent")
    op.drop_column("user", "deleted_at")
    op.drop_column("user", "phone")

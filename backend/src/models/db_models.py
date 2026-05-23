"""SQLAlchemy ORM 모델 — 회원·출생정보·대화·구독·사전예약.

⚠ 활성화 조건: 환경변수 `DATABASE_URL` 설정 + Alembic 마이그레이션 적용.
미설정 시 API는 이 테이블을 사용하지 않는다(현재 운영은 stateless).

PII 보호: birth_records.encrypted_payload는 `PII_ENCRYPTION_KEY`로
컬럼 암호화 예정(KMS·Fernet). 본 파일에는 컬럼 정의만 두고 암호화 로직은
서비스 계층에 두어 교체 가능하게 한다.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Plan(StrEnum):
    """구독 요금제 식별자."""

    STANDARD = "standard"
    PREMIUM = "premium"
    PRO = "pro"  # 단건


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PENDING = "pending"


# ── User ──────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))  # email/pw 인증 시
    oauth_provider: Mapped[str | None] = mapped_column(String(40))  # "kakao" | "google" 등
    oauth_subject: Mapped[str | None] = mapped_column(String(255))  # 제공자측 user id
    name: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    birth_records: Mapped[list[BirthRecord]] = relationship(back_populates="user")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="user")
    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="user")

    __table_args__ = (
        UniqueConstraint("oauth_provider", "oauth_subject", name="uq_user_oauth"),
    )


# ── BirthRecord (출생정보, 암호화 컬럼) ───────────────────────
class BirthRecord(Base):
    __tablename__ = "birth_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    label: Mapped[str | None] = mapped_column(String(80))  # 본인/배우자/자녀 등
    # PII: 평문 저장 금지. Fernet/KMS로 암호화된 JSON payload만 보관.
    # 평문 구조: gender, calendar, year, month, day, hour, minute,
    # longitude, latitude, timezone, is_leap_month
    encrypted_payload: Mapped[bytes] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="birth_records")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="birth_record")


# ── Conversation (대화 세션) ──────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    birth_record_id: Mapped[int] = mapped_column(
        ForeignKey("birth_record.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    user: Mapped[User] = relationship(back_populates="conversations")
    birth_record: Mapped[BirthRecord] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


# ── Message (단일 대화 메시지) ────────────────────────────────
class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    basis: Mapped[str | None] = mapped_column(Text)
    citations: Mapped[dict | None] = mapped_column(JSONB)  # [{source, volume}, ...]
    flags: Mapped[dict | None] = mapped_column(JSONB)  # 가드레일 플래그
    model: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


# ── Subscription (구독 상태, PortOne 토큰만 보관) ─────────────
class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(32), nullable=False)  # Plan
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # SubscriptionStatus
    portone_subscription_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    price_krw: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped[User] = relationship(back_populates="subscriptions")


# ── Preorder (현재는 함수 로그/웹훅로 수집, DB 도입 후 승격) ──
class Preorder(Base):
    __tablename__ = "preorder"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(80))
    plan: Mapped[str] = mapped_column(String(32), default="undecided")
    source: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ── ValidationCase mirror (자문위원 승인 케이스 DB 미러; 선택) ──
class ValidationCaseRow(Base):
    __tablename__ = "validation_case"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(240), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(80))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accuracy_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

"""SQLAlchemy ORM 모델 — BM v2 반영 (4티어 + 자문위원 + 결정 추적 + Family).

⚠ 활성화 조건: 환경변수 `DATABASE_URL` 설정 + Alembic 마이그레이션 적용.
미설정 시 API는 이 테이블을 사용하지 않는다(현재 운영은 stateless).

PII 보호: birth_records.encrypted_payload는 `PII_ENCRYPTION_KEY`로
컬럼 암호화 예정(KMS·Fernet). 본 파일에는 컬럼 정의만 두고 암호화 로직은
서비스 계층에 두어 교체 가능하게 한다.

BM v2 핵심 데이터 모델:
  ❶ 결정 추적 데이터셋 (decision_log) — 진짜 해자 ❶
  ❷ 자문위원 풀 (advisor + advisor_session) — 진짜 해자 ❷
  ❸ Family 패키지 (family_member + 가족 동의) — 단위경제 #7 함정 차단
  ❹ Payment + RefundRequest — 단계별 청약철회 회수율
  ❺ Subscription 4티어 + 자동갱신 opt-in
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


# ── Enums (BM v2 반영) ───────────────────────────────────────
class Plan(StrEnum):
    """BM v2 4티어 + 단건."""

    BASIC = "basic"          # 49,000원/년 (Self-serve)
    STANDARD = "standard"    # 149,000원/년 (Self-serve)
    PREMIUM = "premium"      # 390,000원/년 (Self-serve + TM)
    FAMILY = "family"        # 590,000원/년 (TM 우선)
    PRO = "pro"              # 단건 99,000원 (1회 리포트)


class Channel(StrEnum):
    """획득 채널 — 어트리뷰션 분쟁 차단."""

    SELF_SERVE = "self_serve"  # 앱·웹 자가 가입
    TM = "tm"                  # 텔레마케팅
    B2B = "b2b"                # 기업 영업


class SubscriptionStatus(StrEnum):
    PENDING = "pending"        # 결제 진행 중
    ACTIVE = "active"          # 활성
    PAUSED = "paused"          # 일시정지 (사용자 요청)
    CANCELED = "canceled"      # 해지 (만료일까지 사용 가능)
    EXPIRED = "expired"        # 만료 (사용 불가)
    REFUNDED = "refunded"      # 환불 완료 (즉시 종료)


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentProvider(StrEnum):
    TOSS = "toss"
    KAKAO = "kakao"
    PORTONE = "portone"  # 통합 게이트웨이
    MANUAL = "manual"    # TM 채널 수기 처리


class RefundStage(StrEnum):
    """청약철회 단계별 수수료 회수율 (TM 정산 자동화)."""

    WITHIN_7D = "within_7d"        # 100% 회수 (법정 청약철회)
    WITHIN_30D = "within_30d"      # 50% 회수
    WITHIN_90D = "within_90d"      # 25% 회수
    AFTER_90D = "after_90d"        # 0% 회수


class DecisionType(StrEnum):
    """결정 도우미 카테고리 — 데이터 자산화 ❶."""

    CAREER = "career"            # 이직·진로
    BUSINESS = "business"        # 사업·창업
    MARRIAGE = "marriage"        # 결혼
    DIVORCE = "divorce"          # 이혼
    MOVING = "moving"            # 이사·이주
    INVESTMENT = "investment"    # 투자
    EDUCATION = "education"      # 학업·자녀 교육
    HEALTH = "health"            # 건강
    OTHER = "other"


class AdvisorSessionStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELED = "canceled"


class FamilyRelation(StrEnum):
    """Family 패키지 가족 관계 — 14세+ 동의 처리 게이트."""

    SELF = "self"
    SPOUSE = "spouse"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    OTHER = "other"


class ConsentStatus(StrEnum):
    """14세 이상 자녀·제3자 본인 동의 상태."""

    NOT_REQUIRED = "not_required"  # 14세 미만 / 부모 본인
    REQUESTED = "requested"        # 동의 링크 발송
    GRANTED = "granted"            # 본인 동의 완료
    REJECTED = "rejected"
    EXPIRED = "expired"


# ── User ──────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    oauth_provider: Mapped[str | None] = mapped_column(String(40))  # kakao | apple | google
    oauth_subject: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(40))  # TM 채널 수기 입력용
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # soft delete
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # 마케팅 동의 (옵션)
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    marketing_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 일진 알림 설정 (K-cron 발송 기준, 자평 가드: opt-in + 끄기 1depth)
    notif_daily_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    notif_daily_time_hhmm: Mapped[str] = mapped_column(
        String(5), default="08:00", nullable=False,
    )
    # 부정 통변(주의·흉) 알림 끄기 (불안 마케팅 차단, 자평 가드 #9)
    notif_negative_muted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )

    birth_records: Mapped[list[BirthRecord]] = relationship(back_populates="user")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="user")
    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="user")
    decisions: Mapped[list[DecisionLog]] = relationship(back_populates="user")
    family_members: Mapped[list[FamilyMember]] = relationship(back_populates="user")
    push_tokens: Mapped[list[PushToken]] = relationship(back_populates="user")

    __table_args__ = (
        UniqueConstraint("oauth_provider", "oauth_subject", name="uq_user_oauth"),
    )


# ── BirthRecord (출생정보, 암호화 컬럼) ───────────────────────
class BirthRecord(Base):
    __tablename__ = "birth_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    label: Mapped[str | None] = mapped_column(String(80))  # 본인 / 배우자 / 자녀 등
    # PII: 평문 저장 금지. Fernet/KMS 암호화 payload.
    encrypted_payload: Mapped[bytes] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="birth_records")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="birth_record")


# ── FamilyMember (BM v2 Family 패키지 — 14세+ 자녀 동의 게이트) ──
class FamilyMember(Base):
    __tablename__ = "family_member"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )  # Family 가입자 본인 (가족 대표)
    birth_record_id: Mapped[int] = mapped_column(
        ForeignKey("birth_record.id", ondelete="CASCADE"), index=True
    )
    relation: Mapped[str] = mapped_column(String(32), nullable=False)  # FamilyRelation
    is_minor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 14세 미만
    requires_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 14세+
    consent_status: Mapped[str] = mapped_column(
        String(32), default=ConsentStatus.NOT_REQUIRED.value, nullable=False,
    )
    consent_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 동의 링크 발송지 (email/phone)
    consent_contact: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="family_members")


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
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    basis: Mapped[str | None] = mapped_column(Text)
    citations: Mapped[dict | None] = mapped_column(JSONB)
    flags: Mapped[dict | None] = mapped_column(JSONB)
    model: Mapped[str | None] = mapped_column(String(80))
    # 자평 정체성 모니터링: tone_down 후 잔여 금지 어휘 (없으면 빈 배열)
    tone_audit: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True,
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


# ── Subscription (BM v2 4티어 + 자동갱신 opt-in) ──────────────
class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(32), nullable=False)  # Plan
    # SubscriptionStatus
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)  # Channel
    # 어트리뷰션
    tm_partner_code: Mapped[str | None] = mapped_column(String(40), index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    price_krw: Mapped[int] = mapped_column(Integer, nullable=False)

    # BM v2: 자동갱신 디폴트 OFF (opt-in) — 다크패턴 규제 차단
    autorenew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    autorenew_optin_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 갱신 알림 추적 (D-30, D-7, D-1)
    renewal_notice_30d_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    renewal_notice_7d_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    renewal_notice_1d_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # PortOne 결제 자동화 토큰 (PCI 범위 X)
    portone_billing_key: Mapped[str | None] = mapped_column(String(128), unique=True)

    user: Mapped[User] = relationship(back_populates="subscriptions")
    payments: Mapped[list[Payment]] = relationship(back_populates="subscription")


# ── Payment (결제 트랜잭션) ──────────────────────────────────
class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscription.id", ondelete="CASCADE"), index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)

    amount_krw: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)   # PaymentStatus
    provider: Mapped[str] = mapped_column(String(32), nullable=False)             # PaymentProvider
    provider_tx_id: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    method: Mapped[str | None] = mapped_column(String(40))  # card / bank / kakao_pay
    receipt_url: Mapped[str | None] = mapped_column(String(500))

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refund_amount_krw: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True,
    )

    subscription: Mapped[Subscription] = relationship(back_populates="payments")
    refund_requests: Mapped[list[RefundRequest]] = relationship(back_populates="payment")


# ── RefundRequest (청약철회 단계별 회수율 — TM 정산) ──────────
class RefundRequest(Base):
    __tablename__ = "refund_request"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payment.id", ondelete="CASCADE"), index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)

    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    days_since_payment: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)         # RefundStage
    refund_amount_krw: Mapped[int] = mapped_column(Integer, nullable=False)

    # TM 채널 수수료 자동 회수 (계약가 × 회수율%)
    tm_commission_clawback_krw: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(String(500))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_by: Mapped[str | None] = mapped_column(String(80))  # 자동 / 운영자 이메일

    payment: Mapped[Payment] = relationship(back_populates="refund_requests")


# ── Advisor (명리 자문위원 풀 — 진짜 해자 ❷) ──────────────────
class Advisor(Base):
    __tablename__ = "advisor"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))

    # 경력·저서·매체 출연 (자격증 어휘 회피 — 카피 가이드라인)
    bio: Mapped[str | None] = mapped_column(Text)
    years_experience: Mapped[int | None] = mapped_column(Integer)
    publications: Mapped[dict | None] = mapped_column(JSONB)  # [{title, year, type}]
    media_appearances: Mapped[dict | None] = mapped_column(JSONB)

    # 계약 (3년 독점 + 위약금 + 지분)
    contract_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contract_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_exclusive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rate_per_session_krw: Mapped[int | None] = mapped_column(Integer)  # 회당 단가

    # 가용 시간
    weekly_hours_max: Mapped[int] = mapped_column(Integer, default=40, nullable=False)

    # 등급 (1급/2급 — 단위경제 검증 #2)
    grade: Mapped[str | None] = mapped_column(String(16))  # tier1 / tier2

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    sessions: Mapped[list[AdvisorSession]] = relationship(back_populates="advisor")


# ── AdvisorSession (1:1 상담 매칭) ───────────────────────────
class AdvisorSession(Base):
    __tablename__ = "advisor_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    advisor_id: Mapped[int] = mapped_column(
        ForeignKey("advisor.id", ondelete="RESTRICT"), index=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscription.id", ondelete="SET NULL"),
    )

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # AdvisorSessionStatus

    # 자평 가이드라인 #7: 녹취 동의 자동 안내
    recording_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recording_url: Mapped[str | None] = mapped_column(String(500))

    # PII 보호: 상담 메모는 암호화
    notes_encrypted: Mapped[bytes | None] = mapped_column(nullable=True)

    # 만족도 (사용자 follow-up)
    satisfaction_score: Mapped[int | None] = mapped_column(Integer)  # 1~10

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now,
    )

    advisor: Mapped[Advisor] = relationship(back_populates="sessions")


# ── DecisionLog (결정 추적 데이터셋 — 진짜 해자 ❶) ──────────
class DecisionLog(Base):
    """사용자 결정 + 6개월 후 만족도 follow-up.

    1만 건 누적 시: "이 격국·일주의 사람이 이런 결정에서 이렇게 만족"
    데이터 자산화. 경쟁사가 카피 불가 — 시간이 필요.
    """

    __tablename__ = "decision_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    birth_record_id: Mapped[int] = mapped_column(
        ForeignKey("birth_record.id", ondelete="CASCADE"), index=True,
    )

    decision_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    # 익명화·집계용: 사주 8자 / 일간 / 격국 / 용신 (PII 분리)
    sajupillars_anon: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # 사용자 입력
    option_a_summary: Mapped[str | None] = mapped_column(Text)
    option_b_summary: Mapped[str | None] = mapped_column(Text)
    user_context: Mapped[str | None] = mapped_column(Text)

    # 자평 자문 (LLM 응답)
    lean: Mapped[str | None] = mapped_column(String(16))  # A / B / balanced
    advisor_response_summary: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(16))

    # Follow-up (3개월 / 6개월 후)
    actual_choice: Mapped[str | None] = mapped_column(String(16))  # A / B / other
    actual_choice_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 만족도 follow-up (3개월 후)
    followup_3m_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    followup_3m_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    followup_3m_satisfaction: Mapped[int | None] = mapped_column(Integer)  # 1~10

    # 만족도 follow-up (6개월 후)
    followup_6m_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    followup_6m_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    followup_6m_satisfaction: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True,
    )

    user: Mapped[User] = relationship(back_populates="decisions")


# ── Preorder (legacy — 향후 marketing leads 로 통합) ─────────
class Preorder(Base):
    __tablename__ = "preorder"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(80))
    plan: Mapped[str] = mapped_column(String(32), default="undecided")
    source: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ── ValidationCase mirror (자문위원 승인 검증 케이스) ─────────
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


# ── PushToken (일진 알림 전송 대상) ──────────────────────────
class PushToken(Base):
    """Expo Push 또는 FCM 토큰 보관.

    한 사용자가 여러 기기(폰·태블릿) 보유 가능 → user_id × token unique.
    """

    __tablename__ = "push_token"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(16), nullable=False)  # ios / android / web
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(255))  # DeviceNotRegistered 등

    user: Mapped[User] = relationship(back_populates="push_tokens")

    __table_args__ = (
        UniqueConstraint("user_id", "token", name="uq_push_token_user_token"),
    )


# ── NotificationLog (발송 감사) ──────────────────────────────
class NotificationLog(Base):
    """푸시 발송 결과 로그 — 감사·디버그·운영 모니터링."""

    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    push_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("push_token.id", ondelete="SET NULL"),
    )
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False)  # "daily_fortune" 등
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # "ok" / "error"
    provider_response: Mapped[dict | None] = mapped_column(JSONB)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True,
    )


# ── RateLimitEvent (감사·모니터링) ────────────────────────────
class RateLimitEvent(Base):
    """레이트 리밋 위반 이벤트 로그 — 봇 탐지·운영 모니터링."""

    __tablename__ = "rate_limit_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ip: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    user_tier: Mapped[str | None] = mapped_column(String(32))
    # user_daily / ip_per_minute / ip_per_day
    layer: Mapped[str] = mapped_column(String(40), nullable=False)
    limit_value: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_count: Mapped[int] = mapped_column(Integer, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    blocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True,
    )

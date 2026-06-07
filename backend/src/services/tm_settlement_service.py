"""TM 파트너 정산 자동화 — partner_code 기반 월간 리포트.

BM v2 TM 채널 본 운영 핵심.

수수료 구조 (디폴트, 파트너별 협상으로 override):
  - Premium  35% — 회당 136,500원
  - Family   40% — 회당 236,000원
  - 갱신 (1년차)  10%
  - 업셀 (티어 업)  차액의 30%
  - 가족 추가 (Family 외 단독)  100,000원/인

볼륨 보너스 (월간):
  - 50건+ : +5%
  - 100건+: +10%

청약철회 단계별 수수료 회수 (RefundStage):
  - WITHIN_7D : 100% 회수
  - WITHIN_30D:  50% 회수
  - WITHIN_90D:  25% 회수
  - AFTER_90D :   0% 회수

순 정산액 = 수수료 매출 − 회수 + 볼륨 보너스

순수 계산 함수는 DB 의존 없음 → 테스트 자유.
DB wrapper 는 DATABASE_URL 활성 시만 작동.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

# ── 디폴트 수수료율 (BM v2) ──────────────────────────────
DEFAULT_COMMISSION_RATE = {
    "premium": 0.35,
    "family": 0.40,
    "basic": 0.0,      # TM 비대상
    "standard": 0.0,   # TM 비대상
    "pro": 0.30,       # 단건 협상
}

# 갱신·업셀·가족 보너스
RENEWAL_RATE = 0.10
UPGRADE_RATE = 0.30
FAMILY_ADD_FEE_KRW = 100_000

# 볼륨 보너스 (월 신규 가입 기준)
VOLUME_BONUS_TIERS = (
    (100, 0.10),   # 100+ → +10%
    (50, 0.05),    # 50+  → +5%
)

# 청약철회 단계별 회수율 (RefundStage → 회수율)
CLAWBACK_RATE = {
    "within_7d": 1.00,    # 100% 회수
    "within_30d": 0.50,
    "within_90d": 0.25,
    "after_90d": 0.0,
}


# ── 데이터 클래스 ────────────────────────────────────────
@dataclass(slots=True)
class SettlementLine:
    """정산 1건 (가입 1건 또는 환불 1건)."""

    payment_id: int
    subscription_id: int
    user_id: int
    plan: str  # premium / family / basic / standard / pro
    paid_at: datetime
    contract_amount_krw: int
    commission_rate: float
    commission_krw: int = 0  # contract × rate

    # 환불 발생 시 (없으면 모두 0)
    refund_at: datetime | None = None
    refund_amount_krw: int = 0
    refund_stage: str | None = None     # RefundStage value
    clawback_rate: float = 0.0
    clawback_krw: int = 0

    # 최종 (commission - clawback)
    net_commission_krw: int = 0


@dataclass(slots=True)
class SettlementReport:
    """월간 정산 리포트."""

    partner_code: str
    period_start: date
    period_end: date

    lines: list[SettlementLine] = field(default_factory=list)

    # 집계
    new_signups: int = 0
    gross_commission_krw: int = 0
    total_clawback_krw: int = 0
    net_commission_krw: int = 0

    # 볼륨 보너스
    volume_bonus_rate: float = 0.0
    volume_bonus_krw: int = 0

    # 최종 정산액 (net + bonus)
    final_settlement_krw: int = 0


# ── 순수 계산 함수 ────────────────────────────────────────
def get_commission_rate(plan: str, overrides: dict[str, float] | None = None) -> float:
    """파트너별 협상 수수료율 override 적용."""
    if overrides and plan in overrides:
        return overrides[plan]
    return DEFAULT_COMMISSION_RATE.get(plan, 0.0)


def compute_volume_bonus_rate(new_signups: int) -> float:
    """월 신규 가입 수에 따른 볼륨 보너스율."""
    for threshold, rate in VOLUME_BONUS_TIERS:
        if new_signups >= threshold:
            return rate
    return 0.0


def compute_clawback(
    commission_krw: int,
    refund_stage: str | None,
) -> tuple[float, int]:
    """청약철회 단계별 수수료 회수액 계산.

    Returns: (회수율, 회수금액)
    """
    if not refund_stage:
        return 0.0, 0
    rate = CLAWBACK_RATE.get(refund_stage, 0.0)
    return rate, int(commission_krw * rate)


def classify_refund_stage(days_since_payment: int) -> str:
    """결제 후 경과일 → RefundStage."""
    if days_since_payment <= 7:
        return "within_7d"
    if days_since_payment <= 30:
        return "within_30d"
    if days_since_payment <= 90:
        return "within_90d"
    return "after_90d"


def build_settlement_line(
    payment: dict[str, Any],
    refund: dict[str, Any] | None,
    commission_overrides: dict[str, float] | None = None,
) -> SettlementLine:
    """단일 가입(+환불) 정보 → SettlementLine.

    payment: {id, subscription_id, user_id, plan, paid_at, amount_krw}
    refund (없으면 None): {amount_krw, requested_at, stage}
    """
    plan = payment["plan"]
    rate = get_commission_rate(plan, commission_overrides)
    contract = int(payment["amount_krw"])
    commission = int(contract * rate)

    line = SettlementLine(
        payment_id=int(payment["id"]),
        subscription_id=int(payment["subscription_id"]),
        user_id=int(payment["user_id"]),
        plan=plan,
        paid_at=payment["paid_at"],
        contract_amount_krw=contract,
        commission_rate=rate,
        commission_krw=commission,
    )

    if refund:
        stage = refund.get("stage") or classify_refund_stage(
            int(refund.get("days_since_payment", 0)),
        )
        rate2, claw = compute_clawback(commission, stage)
        line.refund_at = refund.get("requested_at")
        line.refund_amount_krw = int(refund.get("amount_krw", 0))
        line.refund_stage = stage
        line.clawback_rate = rate2
        line.clawback_krw = claw

    line.net_commission_krw = line.commission_krw - line.clawback_krw
    return line


def aggregate_report(
    partner_code: str,
    period_start: date,
    period_end: date,
    lines: list[SettlementLine],
) -> SettlementReport:
    """SettlementLine 목록 → 월간 집계 리포트."""
    # new_signups: 환불되지 않은 가입만
    new_signups = sum(1 for line in lines if line.clawback_rate < 1.0)
    gross = sum(line.commission_krw for line in lines)
    clawback = sum(line.clawback_krw for line in lines)
    net = gross - clawback

    bonus_rate = compute_volume_bonus_rate(new_signups)
    bonus = int(net * bonus_rate)

    return SettlementReport(
        partner_code=partner_code,
        period_start=period_start,
        period_end=period_end,
        lines=lines,
        new_signups=new_signups,
        gross_commission_krw=gross,
        total_clawback_krw=clawback,
        net_commission_krw=net,
        volume_bonus_rate=bonus_rate,
        volume_bonus_krw=bonus,
        final_settlement_krw=net + bonus,
    )


# ── DB Wrapper (DATABASE_URL 활성 시만) ──────────────────
def _db_enabled() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


async def fetch_partner_settlement(
    partner_code: str,
    period_start: date,
    period_end: date,
    commission_overrides: dict[str, float] | None = None,
) -> SettlementReport:
    """실 DB 에서 해당 partner 의 기간 정산 리포트 생성.

    DB 미설정 시 빈 리포트 반환.
    """
    if not _db_enabled():
        return SettlementReport(
            partner_code=partner_code,
            period_start=period_start,
            period_end=period_end,
        )

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import joinedload

    from src.core.db import _session_factory
    from src.models.db_models import Payment, Subscription

    session: AsyncSession
    async with _session_factory()() as session:
        # 해당 partner 의 모든 가입 + 결제 조회
        period_start_dt = datetime.combine(period_start, datetime.min.time())
        period_end_dt = datetime.combine(period_end + timedelta(days=1), datetime.min.time())

        stmt = (
            select(Payment)
            .join(Subscription, Payment.subscription_id == Subscription.id)
            .where(Subscription.tm_partner_code == partner_code)
            .where(Payment.paid_at >= period_start_dt)
            .where(Payment.paid_at < period_end_dt)
            .where(Payment.status == "succeeded")
            .options(joinedload(Payment.subscription), joinedload(Payment.refund_requests))
        )
        result = await session.execute(stmt)
        payments = result.unique().scalars().all()

        lines: list[SettlementLine] = []
        for p in payments:
            sub = p.subscription
            # 환불 1건만 (가장 최근, 단순화)
            refund_dict = None
            if p.refund_requests:
                r = sorted(p.refund_requests, key=lambda x: x.requested_at)[-1]
                refund_dict = {
                    "amount_krw": r.refund_amount_krw,
                    "requested_at": r.requested_at,
                    "stage": r.stage,
                    "days_since_payment": r.days_since_payment,
                }
            payment_dict = {
                "id": p.id,
                "subscription_id": p.subscription_id,
                "user_id": p.user_id,
                "plan": sub.plan,
                "paid_at": p.paid_at,
                "amount_krw": p.amount_krw,
            }
            lines.append(build_settlement_line(payment_dict, refund_dict, commission_overrides))

        return aggregate_report(partner_code, period_start, period_end, lines)


# ── CSV 출력 ─────────────────────────────────────────────
def report_to_csv(report: SettlementReport) -> str:
    """리포트를 CSV 문자열로 직렬화 (TM 회사 정산 명세 전달용)."""
    lines = [
        "# 자평 TM 파트너 정산 리포트",
        f"# partner_code: {report.partner_code}",
        f"# period: {report.period_start} ~ {report.period_end}",
        f"# new_signups: {report.new_signups}",
        f"# gross_commission_krw: {report.gross_commission_krw:,}",
        f"# total_clawback_krw: {report.total_clawback_krw:,}",
        f"# net_commission_krw: {report.net_commission_krw:,}",
        f"# volume_bonus_rate: {report.volume_bonus_rate:.0%}",
        f"# volume_bonus_krw: {report.volume_bonus_krw:,}",
        f"# final_settlement_krw: {report.final_settlement_krw:,}",
        "",
        "payment_id,subscription_id,user_id,plan,paid_at,contract_krw,"
        "commission_rate,commission_krw,refund_stage,clawback_rate,clawback_krw,net_krw",
    ]
    for line in report.lines:
        lines.append(
            f"{line.payment_id},{line.subscription_id},{line.user_id},{line.plan},"
            f"{line.paid_at.isoformat() if line.paid_at else ''},"
            f"{line.contract_amount_krw},{line.commission_rate:.4f},"
            f"{line.commission_krw},{line.refund_stage or ''},"
            f"{line.clawback_rate:.4f},{line.clawback_krw},{line.net_commission_krw}"
        )
    return "\n".join(lines)

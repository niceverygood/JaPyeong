"""services.tm_settlement_service 단위 테스트.

순수 계산 함수 위주 — DB 의존 없이 정산 로직 검증.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from src.services.tm_settlement_service import (
    CLAWBACK_RATE,
    DEFAULT_COMMISSION_RATE,
    SettlementLine,
    aggregate_report,
    build_settlement_line,
    classify_refund_stage,
    compute_clawback,
    compute_volume_bonus_rate,
    fetch_partner_settlement,
    get_commission_rate,
    report_to_csv,
)


# ── 수수료율 ─────────────────────────────────────────────
def test_default_commission_rates() -> None:
    """BM v2 — Premium 35%, Family 40%."""
    assert get_commission_rate("premium") == 0.35
    assert get_commission_rate("family") == 0.40
    assert get_commission_rate("basic") == 0.0  # TM 비대상
    assert get_commission_rate("standard") == 0.0


def test_commission_override() -> None:
    """파트너별 협상 수수료율 override."""
    overrides = {"premium": 0.40}  # 협상 결과
    assert get_commission_rate("premium", overrides) == 0.40
    assert get_commission_rate("family", overrides) == 0.40  # default 유지


# ── 청약철회 단계 분류 ────────────────────────────────────
@pytest.mark.parametrize("days,stage", [
    (1, "within_7d"),
    (7, "within_7d"),
    (8, "within_30d"),
    (30, "within_30d"),
    (31, "within_90d"),
    (90, "within_90d"),
    (91, "after_90d"),
    (365, "after_90d"),
])
def test_classify_refund_stage(days: int, stage: str) -> None:
    assert classify_refund_stage(days) == stage


# ── Clawback (수수료 회수) ────────────────────────────────
def test_clawback_within_7d() -> None:
    """7일 내 환불 → 100% 회수."""
    rate, amount = compute_clawback(100_000, "within_7d")
    assert rate == 1.0
    assert amount == 100_000


def test_clawback_within_30d() -> None:
    """30일 내 → 50% 회수."""
    rate, amount = compute_clawback(100_000, "within_30d")
    assert rate == 0.5
    assert amount == 50_000


def test_clawback_within_90d() -> None:
    """90일 내 → 25% 회수."""
    rate, amount = compute_clawback(100_000, "within_90d")
    assert rate == 0.25
    assert amount == 25_000


def test_clawback_after_90d() -> None:
    """90일 이후 → 회수 없음."""
    rate, amount = compute_clawback(100_000, "after_90d")
    assert rate == 0.0
    assert amount == 0


def test_clawback_no_refund() -> None:
    """환불 없으면 0."""
    rate, amount = compute_clawback(100_000, None)
    assert rate == 0.0
    assert amount == 0


# ── 볼륨 보너스 ──────────────────────────────────────────
@pytest.mark.parametrize("signups,bonus", [
    (0, 0.0),
    (49, 0.0),
    (50, 0.05),
    (99, 0.05),
    (100, 0.10),
    (200, 0.10),
])
def test_volume_bonus_thresholds(signups: int, bonus: float) -> None:
    assert compute_volume_bonus_rate(signups) == bonus


# ── 단일 SettlementLine 빌드 ──────────────────────────────
def test_build_line_premium_no_refund() -> None:
    """Premium 1건 — 수수료 35% = 136,500원."""
    payment = {
        "id": 1, "subscription_id": 1, "user_id": 100,
        "plan": "premium", "paid_at": datetime.now(UTC),
        "amount_krw": 390_000,
    }
    line = build_settlement_line(payment, refund=None)
    assert line.commission_rate == 0.35
    assert line.commission_krw == 136_500
    assert line.clawback_krw == 0
    assert line.net_commission_krw == 136_500


def test_build_line_family_with_refund_7d() -> None:
    """Family 1건 — 7일 내 환불 → 수수료 100% 회수."""
    payment = {
        "id": 2, "subscription_id": 2, "user_id": 200,
        "plan": "family", "paid_at": datetime.now(UTC),
        "amount_krw": 590_000,
    }
    refund = {
        "amount_krw": 590_000,
        "requested_at": datetime.now(UTC),
        "stage": "within_7d",
    }
    line = build_settlement_line(payment, refund=refund)
    assert line.commission_rate == 0.40
    assert line.commission_krw == 236_000
    assert line.clawback_rate == 1.0
    assert line.clawback_krw == 236_000
    assert line.net_commission_krw == 0


def test_build_line_partner_override() -> None:
    """파트너 협상 시 더 높은 수수료율."""
    payment = {
        "id": 3, "subscription_id": 3, "user_id": 300,
        "plan": "premium", "paid_at": datetime.now(UTC),
        "amount_krw": 390_000,
    }
    overrides = {"premium": 0.40}  # 협상 시 40%
    line = build_settlement_line(payment, refund=None, commission_overrides=overrides)
    assert line.commission_rate == 0.40
    assert line.commission_krw == 156_000


# ── 월간 집계 리포트 ──────────────────────────────────────
def test_aggregate_report_basic() -> None:
    """Premium 70 + Family 30 시뮬."""
    lines: list[SettlementLine] = []
    for i in range(70):
        payment = {
            "id": i, "subscription_id": i, "user_id": i,
            "plan": "premium", "paid_at": datetime.now(UTC),
            "amount_krw": 390_000,
        }
        lines.append(build_settlement_line(payment, refund=None))
    for i in range(70, 100):
        payment = {
            "id": i, "subscription_id": i, "user_id": i,
            "plan": "family", "paid_at": datetime.now(UTC),
            "amount_krw": 590_000,
        }
        lines.append(build_settlement_line(payment, refund=None))

    report = aggregate_report(
        partner_code="TM001",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
        lines=lines,
    )
    # 100건 → 볼륨 보너스 +10%
    assert report.new_signups == 100
    assert report.volume_bonus_rate == 0.10
    # gross = 70 × 136,500 + 30 × 236,000 = 9,555,000 + 7,080,000 = 16,635,000
    assert report.gross_commission_krw == 16_635_000
    assert report.total_clawback_krw == 0
    assert report.net_commission_krw == 16_635_000
    # bonus = 10% × 16,635,000 = 1,663,500
    assert report.volume_bonus_krw == 1_663_500
    assert report.final_settlement_krw == 18_298_500


def test_aggregate_with_15pct_refund() -> None:
    """15% 환불(7일 내) 시 회수율 반영."""
    lines: list[SettlementLine] = []
    # Premium 100건
    for i in range(85):
        payment = {
            "id": i, "subscription_id": i, "user_id": i,
            "plan": "premium", "paid_at": datetime.now(UTC),
            "amount_krw": 390_000,
        }
        lines.append(build_settlement_line(payment, refund=None))
    for i in range(85, 100):
        # 15건 환불
        payment = {
            "id": i, "subscription_id": i, "user_id": i,
            "plan": "premium", "paid_at": datetime.now(UTC),
            "amount_krw": 390_000,
        }
        refund = {
            "amount_krw": 390_000,
            "requested_at": datetime.now(UTC),
            "stage": "within_7d",
        }
        lines.append(build_settlement_line(payment, refund=refund))

    report = aggregate_report("TM001", date(2026, 6, 1), date(2026, 6, 30), lines)
    # 환불 15건은 net signup 에서 제외 → 85건
    assert report.new_signups == 85
    # gross = 100 × 136,500 = 13,650,000
    assert report.gross_commission_krw == 13_650_000
    # clawback = 15 × 136,500 = 2,047,500
    assert report.total_clawback_krw == 2_047_500
    # net = 11,602,500
    assert report.net_commission_krw == 11_602_500
    # 85건 ≥ 50 → 5% bonus
    assert report.volume_bonus_rate == 0.05


def test_aggregate_zero_signups() -> None:
    """가입 0건이면 모든 집계 0."""
    report = aggregate_report("TM002", date(2026, 6, 1), date(2026, 6, 30), [])
    assert report.new_signups == 0
    assert report.gross_commission_krw == 0
    assert report.volume_bonus_rate == 0.0
    assert report.final_settlement_krw == 0


# ── CSV 출력 ─────────────────────────────────────────────
def test_csv_export() -> None:
    payment = {
        "id": 1, "subscription_id": 1, "user_id": 100,
        "plan": "premium", "paid_at": datetime(2026, 6, 15, 10, 0, tzinfo=UTC),
        "amount_krw": 390_000,
    }
    line = build_settlement_line(payment, refund=None)
    report = aggregate_report("TM001", date(2026, 6, 1), date(2026, 6, 30), [line])
    csv = report_to_csv(report)
    assert "TM001" in csv
    assert "premium" in csv
    assert "390000" in csv
    assert "136500" in csv
    assert "payment_id,subscription_id" in csv  # header


# ── DB Wrapper — DATABASE_URL 없음 시 빈 리포트 ──────────
@pytest.mark.asyncio
async def test_fetch_returns_empty_without_db() -> None:
    import os
    os.environ.pop("DATABASE_URL", None)
    report = await fetch_partner_settlement(
        partner_code="TM001",
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 30),
    )
    assert report.partner_code == "TM001"
    assert report.new_signups == 0
    assert report.lines == []


# ── BM v2 정합성 ──────────────────────────────────────────
def test_clawback_rates_match_bm_v2() -> None:
    """청약철회 단계별 회수율이 BM v2 마스터 설계와 일치."""
    assert CLAWBACK_RATE["within_7d"] == 1.0
    assert CLAWBACK_RATE["within_30d"] == 0.5
    assert CLAWBACK_RATE["within_90d"] == 0.25
    assert CLAWBACK_RATE["after_90d"] == 0.0


def test_commission_rates_match_bm_v2() -> None:
    """BM v2 — Premium 35%, Family 40%."""
    assert DEFAULT_COMMISSION_RATE["premium"] == 0.35
    assert DEFAULT_COMMISSION_RATE["family"] == 0.40

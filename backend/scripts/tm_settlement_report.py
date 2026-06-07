"""TM 파트너 월간 정산 리포트 생성 — 운영 cron 스크립트.

실행:
    # 특정 파트너 + 기간
    python -m src.scripts.tm_settlement_report \\
        --partner TM001 --start 2026-06-01 --end 2026-06-30

    # 모든 파트너 (지난 달)
    python -m src.scripts.tm_settlement_report --all --last-month

    # 출력 형식
    --format csv      # CSV 파일로 저장
    --format json     # JSON stdout
    --out reports/    # 저장 디렉토리 (CSV 모드)

권장 cron: 매월 1일 새벽 — 지난달 정산 자동 생성 → 이메일·웹훅 발송

환경변수:
    DATABASE_URL              — 실 DB 연결 (없으면 빈 리포트)
    SETTLEMENT_WEBHOOK_URL    — 결과 자동 발송 (옵션, Slack/Make/Zapier)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

# import 경로 확보 — backend/ 를 sys.path 에 추가 (직접 실행 시)
_THIS = Path(__file__).resolve()
_BACKEND_ROOT = _THIS.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from src.services.tm_settlement_service import (  # noqa: E402
    SettlementReport,
    fetch_partner_settlement,
    report_to_csv,
)


def last_month_range() -> tuple[date, date]:
    """오늘 기준 지난달 1일 ~ 말일."""
    today = date.today()
    first_this_month = today.replace(day=1)
    last_day_last_month = first_this_month - timedelta(days=1)
    first_last_month = last_day_last_month.replace(day=1)
    return first_last_month, last_day_last_month


def report_to_dict(report: SettlementReport) -> dict:
    """JSON serialization 용."""
    return {
        "partner_code": report.partner_code,
        "period_start": report.period_start.isoformat(),
        "period_end": report.period_end.isoformat(),
        "new_signups": report.new_signups,
        "gross_commission_krw": report.gross_commission_krw,
        "total_clawback_krw": report.total_clawback_krw,
        "net_commission_krw": report.net_commission_krw,
        "volume_bonus_rate": report.volume_bonus_rate,
        "volume_bonus_krw": report.volume_bonus_krw,
        "final_settlement_krw": report.final_settlement_krw,
        "lines_count": len(report.lines),
        "lines": [
            {
                **asdict(line),
                "paid_at": line.paid_at.isoformat() if line.paid_at else None,
                "refund_at": line.refund_at.isoformat() if line.refund_at else None,
            }
            for line in report.lines
        ],
    }


async def run_partner(
    partner: str, start: date, end: date,
    out_dir: Path | None,
    fmt: str,
) -> SettlementReport:
    report = await fetch_partner_settlement(partner, start, end)
    if fmt == "csv":
        csv = report_to_csv(report)
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / f"settlement_{partner}_{start.isoformat()}_to_{end.isoformat()}.csv"
            path.write_text(csv, encoding="utf-8")
            print(f"  ✓ {path}")
        else:
            print(csv)
    elif fmt == "json":
        print(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2))
    return report


async def list_all_partners() -> list[str]:
    """DB 에서 활성 파트너 코드 목록 조회. DB 미설정 시 빈 리스트."""
    if not os.environ.get("DATABASE_URL"):
        return []
    from sqlalchemy import distinct, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import Subscription

    session: AsyncSession
    async with _session_factory()() as session:
        stmt = select(distinct(Subscription.tm_partner_code)).where(
            Subscription.tm_partner_code.is_not(None),
        )
        rows = (await session.execute(stmt)).scalars().all()
        return [code for code in rows if code]


async def main() -> int:
    parser = argparse.ArgumentParser(description="자평 TM 파트너 월간 정산 리포트")
    parser.add_argument("--partner", help="파트너 코드 (단건)")
    parser.add_argument("--all", action="store_true", help="모든 활성 파트너")
    parser.add_argument("--start", help="시작일 YYYY-MM-DD")
    parser.add_argument("--end", help="종료일 YYYY-MM-DD")
    parser.add_argument(
        "--last-month", action="store_true",
        help="지난달 1일 ~ 말일 자동 설정 (--start/--end 와 함께 못 씀)",
    )
    parser.add_argument(
        "--format", choices=("csv", "json"), default="csv",
        help="출력 형식 (기본 csv)",
    )
    parser.add_argument(
        "--out", help="CSV 저장 디렉토리 (없으면 stdout)",
    )
    args = parser.parse_args()

    # 기간 결정
    if args.last_month:
        start, end = last_month_range()
    elif args.start and args.end:
        start = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)
    else:
        parser.error("--last-month 또는 (--start AND --end) 필요")

    out_dir = Path(args.out) if args.out else None

    # 파트너 결정
    if args.all:
        partners = await list_all_partners()
        if not partners:
            print("활성 파트너 없음 (DB 미설정 또는 데이터 없음).", file=sys.stderr)
            return 0
    elif args.partner:
        partners = [args.partner]
    else:
        parser.error("--partner 또는 --all 필요")

    print(f"# 자평 TM 정산 리포트 생성 — {start} ~ {end} · {len(partners)} 파트너")
    print(f"# 시작: {datetime.now(UTC).isoformat()}")

    total_settlement = 0
    for p in partners:
        report = await run_partner(p, start, end, out_dir, args.format)
        total_settlement += report.final_settlement_krw
        print(
            f"  [{p}] 가입 {report.new_signups}건 / "
            f"순마진 {report.net_commission_krw:,} / "
            f"보너스 {report.volume_bonus_krw:,} / "
            f"정산 {report.final_settlement_krw:,}",
            file=sys.stderr,
        )

    print(f"# 총 정산액 합: {total_settlement:,}원", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

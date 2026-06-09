"""정기구독 자동청구 cron — 카카오페이 SID 기반 갱신.

매일(또는 6시간 간격) 실행:
  만료 임박(current_period_end <= now + 1일) + autorenew + kakao_sid 보유 +
  status=ACTIVE 구독을 골라 저장된 SID 로 자동청구한다.

Vercel cron 등록 (예):
  schedule: "0 1 * * *"  (매일 새벽 1시 KST 기준 — 갱신은 즉시성 X)

멱등성:
  청구 성공 시 current_period_end 가 +30일 연장되어 다음 실행에서 윈도우를 벗어나
  중복청구되지 않는다(연장 자체가 가드). 실패 시 Payment.FAILED 만 남고 period_end
  유지 → 다음 cron 에서 재시도.

PII: 로그에 평문 식별정보 금지 — user_id / subscription_id 만 기록.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import UTC, datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("subscription_renewal_cron")

# 만료 며칠 전부터 자동청구를 시도할지 (D-1)
RENEWAL_WINDOW_DAYS = 1
# 한 번의 실행에서 처리할 최대 구독 수 (게이트웨이 부하·타임아웃 가드)
BATCH_LIMIT = 500


async def _run() -> dict[str, int]:
    if not os.environ.get("DATABASE_URL"):
        log.warning("DATABASE_URL 미설정 — renewal cron skipped.")
        return {"skipped": 1}

    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import Subscription, SubscriptionStatus
    from src.services.payment_service import (
        PaymentError,
        charge_recurring_subscription,
    )

    counters = {"charged": 0, "failed": 0}
    now = datetime.now(UTC)
    due_before = now + timedelta(days=RENEWAL_WINDOW_DAYS)

    # 1) 대상 구독 ID 수집 (조회 트랜잭션 — 청구는 서비스가 별도 트랜잭션으로 처리)
    session: AsyncSession
    async with _session_factory()() as session:
        stmt = (
            select(Subscription.id)
            .where(and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.autorenew.is_(True),
                Subscription.kakao_sid.is_not(None),
                Subscription.current_period_end.is_not(None),
                Subscription.current_period_end <= due_before,
            ))
            .order_by(Subscription.current_period_end)
            .limit(BATCH_LIMIT)
        )
        due_ids = [row[0] for row in (await session.execute(stmt)).all()]

    log.info("renewal cron: %d due subscription(s)", len(due_ids))

    # 2) 건별 자동청구
    for sub_id in due_ids:
        try:
            result = await charge_recurring_subscription(sub_id)
            counters["charged"] += 1
            log.info(
                "renewal charged subscription=%s payment=%s period_end=%s",
                sub_id, result.get("payment_id"), result.get("current_period_end"),
            )
        except PaymentError as e:
            counters["failed"] += 1
            log.warning("renewal failed subscription=%s err=%s", sub_id, e)
        except Exception as e:  # noqa: BLE001
            counters["failed"] += 1
            log.exception("renewal exception subscription=%s err=%s", sub_id, e)

    log.info("subscription_renewal_cron done: %s", counters)
    return counters


if __name__ == "__main__":
    result = asyncio.run(_run())
    if result.get("failed", 0) > 0:
        sys.exit(1)

"""결정 로그 follow-up cron — 진짜 해자 ❶ 데이터 누적.

매시간 실행:
  1. followup_3m_due_at <= now AND followup_3m_sent_at IS NULL → 3개월 발송
  2. followup_6m_due_at <= now AND followup_6m_sent_at IS NULL → 6개월 발송

Vercel cron 등록:
  schedule: "0 */6 * * *"  (6시간 간격이면 충분 — follow-up 은 즉시성 X)

발송 후 followup_Nm_sent_at = now (재발송 차단).
실패 시 별도 retry 없음 — 운영자가 NotificationLog 보고 수동 조치.

PII: 로그·예외 메시지에 phone 평문 절대 X. masked 만.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import UTC, datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("decision_followup_cron")


async def _run() -> dict[str, int]:
    if not os.environ.get("DATABASE_URL"):
        log.warning("DATABASE_URL 미설정 — follow-up cron skipped.")
        return {"skipped": 1}

    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import DecisionLog, User
    from src.services.solapi_service import mask_phone, send_followup

    counters = {"sent_3m": 0, "sent_6m": 0, "skipped_no_phone": 0, "failed": 0}
    now = datetime.now(UTC)

    session: AsyncSession
    async with _session_factory()() as session:
        # 3개월
        stmt_3m = (
            select(DecisionLog, User)
            .join(User, DecisionLog.user_id == User.id)
            .where(and_(
                DecisionLog.followup_3m_due_at.is_not(None),
                DecisionLog.followup_3m_due_at <= now,
                DecisionLog.followup_3m_sent_at.is_(None),
                User.deleted_at.is_(None),
            ))
            .limit(500)
        )
        rows_3m = (await session.execute(stmt_3m)).all()
        for log_row, user in rows_3m:
            if not user.phone:
                counters["skipped_no_phone"] += 1
                continue
            label = log_row.decision_type or "결정"
            try:
                r = await send_followup(user.phone, months=3, decision_label=label)
                if r.success:
                    log_row.followup_3m_sent_at = now
                    counters["sent_3m"] += 1
                    log.info(
                        "followup_3m sent user=%s phone=%s channel=%s",
                        user.id, mask_phone(user.phone), r.channel,
                    )
                else:
                    counters["failed"] += 1
                    log.warning(
                        "followup_3m failed user=%s err=%s",
                        user.id, r.error,
                    )
            except Exception as e:  # noqa: BLE001
                counters["failed"] += 1
                log.exception("followup_3m exception user=%s err=%s", user.id, e)

        # 6개월
        stmt_6m = (
            select(DecisionLog, User)
            .join(User, DecisionLog.user_id == User.id)
            .where(and_(
                DecisionLog.followup_6m_due_at.is_not(None),
                DecisionLog.followup_6m_due_at <= now,
                DecisionLog.followup_6m_sent_at.is_(None),
                User.deleted_at.is_(None),
            ))
            .limit(500)
        )
        rows_6m = (await session.execute(stmt_6m)).all()
        for log_row, user in rows_6m:
            if not user.phone:
                counters["skipped_no_phone"] += 1
                continue
            label = log_row.decision_type or "결정"
            try:
                r = await send_followup(user.phone, months=6, decision_label=label)
                if r.success:
                    log_row.followup_6m_sent_at = now
                    counters["sent_6m"] += 1
                    log.info(
                        "followup_6m sent user=%s phone=%s channel=%s",
                        user.id, mask_phone(user.phone), r.channel,
                    )
                else:
                    counters["failed"] += 1
            except Exception as e:  # noqa: BLE001
                counters["failed"] += 1
                log.exception("followup_6m exception user=%s err=%s", user.id, e)

        await session.commit()

    log.info("decision_followup_cron done: %s", counters)
    return counters


if __name__ == "__main__":
    result = asyncio.run(_run())
    if result.get("failed", 0) > 0:
        sys.exit(1)

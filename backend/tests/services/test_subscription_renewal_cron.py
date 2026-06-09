"""subscription_renewal_cron — 정기구독 자동청구 cron 단위 테스트.

- DATABASE_URL 미설정 시 skip
- due 구독 ID 수집 → 건별 charge 호출 + 성공/실패 카운트
- charge 실패해도 다른 구독은 계속 처리 (격리)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from scripts.subscription_renewal_cron import _run
from src.services.payment_service import PaymentError


async def test_skips_without_db() -> None:
    with patch.dict(os.environ, {}, clear=True):
        result = await _run()
    assert result == {"skipped": 1}


def _fake_session_factory(due_ids: list[int]):
    """due_ids 를 반환하는 execute().all() 을 가진 세션 팩토리 목."""
    rows = [(i,) for i in due_ids]
    exec_result = MagicMock()
    exec_result.all.return_value = rows

    session = MagicMock()
    session.execute = AsyncMock(return_value=exec_result)

    @asynccontextmanager
    async def _ctx():
        yield session

    factory = MagicMock(return_value=_ctx())
    # _session_factory() -> factory ; factory() -> async ctx
    return MagicMock(return_value=factory), session


async def test_charges_due_subscriptions() -> None:
    factory, _session = _fake_session_factory([10, 20, 30])
    charge = AsyncMock(side_effect=[
        {"payment_id": 1, "current_period_end": "2026-08-01T00:00:00+00:00"},
        {"payment_id": 2, "current_period_end": "2026-08-01T00:00:00+00:00"},
        {"payment_id": 3, "current_period_end": "2026-08-01T00:00:00+00:00"},
    ])
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}, clear=False), \
         patch("src.core.db._session_factory", factory), \
         patch(
             "src.services.payment_service.charge_recurring_subscription",
             charge,
         ):
        result = await _run()
    assert result == {"charged": 3, "failed": 0}
    assert charge.await_count == 3
    assert [c.args[0] for c in charge.await_args_list] == [10, 20, 30]


async def test_isolates_charge_failures() -> None:
    factory, _session = _fake_session_factory([10, 20])
    charge = AsyncMock(side_effect=[
        PaymentError("카카오 정기청구 실패"),
        {"payment_id": 2, "current_period_end": "2026-08-01T00:00:00+00:00"},
    ])
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}, clear=False), \
         patch("src.core.db._session_factory", factory), \
         patch(
             "src.services.payment_service.charge_recurring_subscription",
             charge,
         ):
        result = await _run()
    assert result == {"charged": 1, "failed": 1}


async def test_no_due_subscriptions() -> None:
    factory, _session = _fake_session_factory([])
    charge = AsyncMock()
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://x"}, clear=False), \
         patch("src.core.db._session_factory", factory), \
         patch(
             "src.services.payment_service.charge_recurring_subscription",
             charge,
         ):
        result = await _run()
    assert result == {"charged": 0, "failed": 0}
    charge.assert_not_awaited()

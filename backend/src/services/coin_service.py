"""코인 지갑 서비스 — 충전/차감/환불/원장.

원칙:
  - 모든 잔액 변경은 한 트랜잭션 안에서 지갑 행을 FOR UPDATE 로 잠그고 수행
    → 동시 요청 더블스펜드/경합 차단(사용자별 직렬화).
  - 멱등 키(idempotency_key)로 IAP transaction_id·클라이언트 요청 중복을 차단
    → 네트워크 재시도로 코인이 2번 적립/차감되지 않음.
  - 지갑 생성은 INSERT ... ON CONFLICT DO NOTHING 으로 경합 안전.
  - balance 는 항상 원장(coin_transaction) 합과 일치(balance_after 기록).
DB 미설정 시 모든 함수 raise(코인은 인프라 필수).
"""

from __future__ import annotations

import os
from typing import Any


class CoinError(Exception):
    """코인 도메인 에러."""


class InsufficientCoins(CoinError):
    """잔액 부족."""


class CoinDatabaseUnavailable(CoinError):
    """DB 미설정/장애."""


def _db_required() -> None:
    if not os.environ.get("DATABASE_URL"):
        raise CoinDatabaseUnavailable("DATABASE_URL 미설정 — 코인 기능 사용 불가.")


async def _ensure_wallet_locked(session, user_id: int):  # noqa: ANN001
    """지갑을 보장 생성(ON CONFLICT) 후 FOR UPDATE 로 잠가 반환."""
    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from src.models.db_models import CoinWallet

    stmt = (
        pg_insert(CoinWallet)
        .values(user_id=user_id, balance=0, lifetime_charged=0, lifetime_spent=0)
        .on_conflict_do_nothing(index_elements=["user_id"])
    )
    await session.execute(stmt)
    return (
        await session.execute(
            select(CoinWallet).where(CoinWallet.user_id == user_id).with_for_update()
        )
    ).scalar_one()


async def _find_by_idem(session, idem: str | None):  # noqa: ANN001
    if not idem:
        return None
    from sqlalchemy import select

    from src.models.db_models import CoinTransaction

    return (
        await session.execute(
            select(CoinTransaction).where(CoinTransaction.idempotency_key == idem)
        )
    ).scalar_one_or_none()


async def get_balance(user_id: int) -> int:
    """현재 코인 잔액 (지갑 없으면 0). 읽기 전용."""
    _db_required()
    from sqlalchemy import select

    from src.core.db import _session_factory
    from src.models.db_models import CoinWallet

    async with _session_factory()() as session:
        w = (
            await session.execute(
                select(CoinWallet).where(CoinWallet.user_id == user_id)
            )
        ).scalar_one_or_none()
        return w.balance if w else 0


async def charge(
    user_id: int,
    coins: int,
    bonus: int = 0,
    payment_id: int | None = None,
    idempotency_key: str | None = None,
    memo: str | None = None,
) -> dict[str, Any]:
    """코인 충전(결제 적립 + 보너스). 멱등 — 같은 키 재요청은 재적립하지 않음."""
    _db_required()
    if coins <= 0:
        raise CoinError("충전 코인은 0보다 커야 합니다.")
    from src.core.db import _session_factory
    from src.models.db_models import CoinTransaction, CoinTxnKind

    async with _session_factory()() as session:
        w = await _ensure_wallet_locked(session, user_id)  # 사용자별 직렬화
        dup = await _find_by_idem(session, idempotency_key)
        if dup is not None:
            return {"balance": w.balance, "credited": 0, "duplicate": True}

        w.balance += coins
        w.lifetime_charged += coins
        session.add(
            CoinTransaction(
                wallet_id=w.id, user_id=user_id, kind=CoinTxnKind.CHARGE,
                amount=coins, balance_after=w.balance, payment_id=payment_id,
                idempotency_key=idempotency_key, memo=memo,
            )
        )
        if bonus > 0:
            w.balance += bonus
            w.lifetime_charged += bonus
            session.add(
                CoinTransaction(
                    wallet_id=w.id, user_id=user_id, kind=CoinTxnKind.BONUS,
                    amount=bonus, balance_after=w.balance, payment_id=payment_id,
                    idempotency_key=(f"{idempotency_key}:bonus" if idempotency_key else None),
                    memo="충전 보너스",
                )
            )
        await session.commit()
        return {"balance": w.balance, "credited": coins + bonus, "duplicate": False}


async def spend(
    user_id: int,
    item_code: str,
    cost: int,
    idempotency_key: str | None = None,
    memo: str | None = None,
) -> dict[str, Any]:
    """단건 상품 코인 차감. 잔액 부족 시 InsufficientCoins. 멱등."""
    _db_required()
    if cost <= 0:
        raise CoinError("차감 코인은 0보다 커야 합니다.")
    from src.core.db import _session_factory
    from src.models.db_models import CoinTransaction, CoinTxnKind

    async with _session_factory()() as session:
        w = await _ensure_wallet_locked(session, user_id)
        dup = await _find_by_idem(session, idempotency_key)
        if dup is not None:
            return {
                "balance": w.balance, "charged": 0,
                "duplicate": True, "txn_id": dup.id,
            }
        if w.balance < cost:
            raise InsufficientCoins(
                f"코인이 부족합니다. (필요 {cost}, 보유 {w.balance})"
            )
        w.balance -= cost
        w.lifetime_spent += cost
        txn = CoinTransaction(
            wallet_id=w.id, user_id=user_id, kind=CoinTxnKind.SPEND,
            amount=-cost, balance_after=w.balance, item_code=item_code,
            idempotency_key=idempotency_key, memo=memo,
        )
        session.add(txn)
        await session.flush()
        txn_id = txn.id
        await session.commit()
        return {
            "balance": w.balance, "charged": cost,
            "duplicate": False, "txn_id": txn_id,
        }


async def refund(
    user_id: int,
    amount: int,
    memo: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """차감 환원(콘텐츠 생성 실패 보상 등). 멱등."""
    _db_required()
    if amount <= 0:
        raise CoinError("환불 코인은 0보다 커야 합니다.")
    from src.core.db import _session_factory
    from src.models.db_models import CoinTransaction, CoinTxnKind

    async with _session_factory()() as session:
        w = await _ensure_wallet_locked(session, user_id)
        dup = await _find_by_idem(session, idempotency_key)
        if dup is not None:
            return {"balance": w.balance, "refunded": 0, "duplicate": True}
        # lifetime_spent 는 누적(gross) 지표 — 환불로 줄이지 않는다(원장 합과의 감사 정합성).
        w.balance += amount
        session.add(
            CoinTransaction(
                wallet_id=w.id, user_id=user_id, kind=CoinTxnKind.REFUND,
                amount=amount, balance_after=w.balance,
                idempotency_key=idempotency_key, memo=memo,
            )
        )
        await session.commit()
        return {"balance": w.balance, "refunded": amount, "duplicate": False}


async def ledger(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    """최근 거래 원장 (최신순)."""
    _db_required()
    from sqlalchemy import desc, select

    from src.core.db import _session_factory
    from src.models.db_models import CoinTransaction

    limit = max(1, min(limit, 100))
    async with _session_factory()() as session:
        rows = (
            await session.execute(
                select(CoinTransaction)
                .where(CoinTransaction.user_id == user_id)
                .order_by(desc(CoinTransaction.created_at), desc(CoinTransaction.id))
                .limit(limit)
            )
        ).scalars().all()
        return [
            {
                "id": t.id,
                "kind": t.kind,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "item_code": t.item_code,
                "memo": t.memo,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in rows
        ]

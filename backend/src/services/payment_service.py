"""결제 서비스 — Toss/Kakao Pay 통합 (PortOne 옵션).

설계:
  1. checkout 요청 → 결제 의도(payment.PENDING) + subscription(PENDING) 생성
  2. 외부 결제 게이트웨이로 redirect URL 발급
  3. webhook 또는 confirm 호출 시 결제 검증 → 활성화
  4. autorenew 는 default OFF (BM v2). opt-in 별도 API.

가격 정책 (BM v2 — 카카오페이 월 정기결제: 연회비 ÷ 12 월분할):
  - basic    4,083원/월   (연 49,000)
  - standard 12,417원/월  (연 149,000)
  - premium  32,500원/월  (연 390,000)
  - family   49,167원/월  (연 590,000)
  ※ 카카오페이 정기결제는 연 단위 입점 불가 → 월 자동청구로 운영한다.

외부 SDK 어댑터:
  - TossPaymentAdapter (실제 HTTP)
  - KakaoPayAdapter (실제 HTTP)
  - MockPaymentAdapter (테스트 + 키 미설정 환경)

DB 미설정 시 모든 함수 raise (결제는 인프라 필수).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import httpx

PLAN_PRICES: dict[str, int] = {
    "basic": 4_083,      # 연 49,000 ÷ 12
    "standard": 12_417,  # 연 149,000 ÷ 12
    "premium": 32_500,   # 연 390,000 ÷ 12
    "family": 49_167,    # 연 590,000 ÷ 12
}


class PaymentError(Exception):
    """결제 도메인 에러."""


def _db_required() -> None:
    if not os.environ.get("DATABASE_URL"):
        raise PaymentError("DATABASE_URL 미설정 — 결제 기능 사용 불가.")


def validate_plan(plan: str) -> int:
    """plan 코드 → 가격 (원). 잘못된 plan 이면 raise."""
    price = PLAN_PRICES.get(plan)
    if price is None:
        raise PaymentError(f"알 수 없는 plan: {plan}")
    return price


# ── 어댑터 인터페이스 ────────────────────────────────────
@dataclass(slots=True, frozen=True)
class CheckoutSession:
    """결제 게이트웨이가 발급한 결제 세션."""

    provider: str            # toss / kakao / mock
    redirect_url: str        # 사용자가 이동할 URL
    provider_session_id: str # 게이트웨이의 세션·결제 키


@dataclass(slots=True, frozen=True)
class ConfirmResult:
    """결제 confirm 응답 정규화."""

    provider_tx_id: str
    amount_krw: int
    method: str | None
    receipt_url: str | None
    raw: dict[str, Any]
    # 정기결제 SID — 정기 CID 로 첫 승인 시에만 채워짐 (단건은 None)
    billing_sid: str | None = None


class PaymentAdapter(Protocol):
    name: str

    async def create_checkout(
        self,
        amount_krw: int,
        order_name: str,
        order_id: str,
        success_url: str,
        fail_url: str,
        recurring: bool = False,
    ) -> CheckoutSession: ...

    async def confirm(
        self,
        provider_session_id: str,
        amount_krw: int,
        extra: dict[str, Any] | None = None,
    ) -> ConfirmResult: ...

    async def refund(
        self,
        provider_tx_id: str,
        amount_krw: int,
        reason: str,
    ) -> dict[str, Any]: ...


# ── 어댑터 구현 ──────────────────────────────────────────
class TossPaymentAdapter:
    """토스페이먼츠 — Payments v1 SDK (server confirm 흐름)."""

    name = "toss"
    BASE = "https://api.tosspayments.com/v1"

    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key

    def _auth(self) -> dict[str, str]:
        import base64
        encoded = base64.b64encode(f"{self.secret_key}:".encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    async def create_checkout(
        self,
        amount_krw: int,
        order_name: str,
        order_id: str,
        success_url: str,
        fail_url: str,
        recurring: bool = False,
    ) -> CheckoutSession:
        # 토스는 클라이언트 SDK 로 직접 결제창을 호출 → 우리는 paymentKey 만 안내.
        # 서버는 success_url 로 받은 paymentKey 를 confirm 호출.
        # (토스 빌링/정기는 별도 billingKey 흐름 — 현재는 단건만 지원, recurring 무시)
        return CheckoutSession(
            provider="toss",
            redirect_url=f"{success_url}?orderId={order_id}&amount={amount_krw}",
            provider_session_id=order_id,
        )

    async def confirm(
        self,
        provider_session_id: str,
        amount_krw: int,
        extra: dict[str, Any] | None = None,
    ) -> ConfirmResult:
        if not extra or "paymentKey" not in extra:
            raise PaymentError("토스 confirm 에 paymentKey 누락")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.BASE}/payments/confirm",
                headers={**self._auth(), "Content-Type": "application/json"},
                json={
                    "paymentKey": extra["paymentKey"],
                    "orderId": provider_session_id,
                    "amount": amount_krw,
                },
            )
            if resp.status_code >= 400:
                raise PaymentError(f"토스 confirm 실패 {resp.status_code}: {resp.text[:200]}")
            data = resp.json()
        return ConfirmResult(
            provider_tx_id=data.get("paymentKey", extra["paymentKey"]),
            amount_krw=int(data.get("totalAmount", amount_krw)),
            method=data.get("method"),
            receipt_url=(data.get("receipt") or {}).get("url"),
            raw=data,
        )

    async def refund(
        self,
        provider_tx_id: str,
        amount_krw: int,
        reason: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.BASE}/payments/{provider_tx_id}/cancel",
                headers={**self._auth(), "Content-Type": "application/json"},
                json={"cancelReason": reason, "cancelAmount": amount_krw},
            )
            if resp.status_code >= 400:
                raise PaymentError(f"토스 환불 실패: {resp.text[:200]}")
            return resp.json()


class KakaoPayAdapter:
    """카카오페이 — 단건결제 + 정기결제(subscription).

    정기결제 흐름:
      1. ready(recurring=True) → 정기 CID 로 결제준비 → tid + 인증 redirect
      2. approve → 첫 결제 승인 + **SID(정기결제 키)** 발급 → 이후 자동청구에 사용
      3. pay_subscription(sid) → 2회차부터 사용자 인증 없이 자동청구
      4. inactivate_subscription(sid) → SID 폐기(정기결제 해지)
    """

    name = "kakao"
    BASE = "https://kapi.kakao.com/v1/payment"

    def __init__(
        self,
        admin_key: str,
        cid: str = "TC0ONETIME",
        subscription_cid: str = "TCSUBSCRIP",
    ) -> None:
        self.admin_key = admin_key
        self.cid = cid                          # 단건 CID (TC0ONETIME=테스트)
        self.subscription_cid = subscription_cid  # 정기 CID (TCSUBSCRIP=테스트)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"KakaoAK {self.admin_key}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        }

    def _cid(self, recurring: bool) -> str:
        return self.subscription_cid if recurring else self.cid

    async def create_checkout(
        self,
        amount_krw: int,
        order_name: str,
        order_id: str,
        success_url: str,
        fail_url: str,
        recurring: bool = False,
    ) -> CheckoutSession:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.BASE}/ready",
                headers=self._headers(),
                data={
                    "cid": self._cid(recurring),
                    "partner_order_id": order_id,
                    "partner_user_id": order_id,
                    "item_name": order_name,
                    "quantity": 1,
                    "total_amount": amount_krw,
                    "tax_free_amount": 0,
                    "approval_url": success_url,
                    "fail_url": fail_url,
                    "cancel_url": fail_url,
                },
            )
            if resp.status_code >= 400:
                raise PaymentError(f"카카오 ready 실패: {resp.text[:200]}")
            data = resp.json()
        return CheckoutSession(
            provider="kakao",
            redirect_url=data["next_redirect_pc_url"],
            provider_session_id=data["tid"],
        )

    async def confirm(
        self,
        provider_session_id: str,
        amount_krw: int,
        extra: dict[str, Any] | None = None,
    ) -> ConfirmResult:
        if not extra or "pg_token" not in extra:
            raise PaymentError("카카오 confirm 에 pg_token 누락")
        recurring = bool(extra.get("recurring"))
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.BASE}/approve",
                headers=self._headers(),
                data={
                    "cid": self._cid(recurring),
                    "tid": provider_session_id,
                    "partner_order_id": extra.get("order_id", provider_session_id),
                    "partner_user_id": extra.get("user_id", provider_session_id),
                    "pg_token": extra["pg_token"],
                },
            )
            if resp.status_code >= 400:
                raise PaymentError(f"카카오 approve 실패: {resp.text[:200]}")
            data = resp.json()
        return ConfirmResult(
            provider_tx_id=data.get("aid", provider_session_id),
            amount_krw=int((data.get("amount") or {}).get("total", amount_krw)),
            method="kakao_pay",
            receipt_url=None,
            raw=data,
            billing_sid=data.get("sid"),  # 정기 CID 승인 시에만 존재
        )

    async def pay_subscription(
        self,
        sid: str,
        amount_krw: int,
        order_name: str,
        order_id: str,
        user_id: str,
    ) -> ConfirmResult:
        """저장된 SID 로 2회차 이후 자동청구 (사용자 인증 불필요)."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.BASE}/subscription",
                headers=self._headers(),
                data={
                    "cid": self.subscription_cid,
                    "sid": sid,
                    "partner_order_id": order_id,
                    "partner_user_id": user_id,
                    "item_name": order_name,
                    "quantity": 1,
                    "total_amount": amount_krw,
                    "tax_free_amount": 0,
                },
            )
            if resp.status_code >= 400:
                raise PaymentError(f"카카오 정기청구 실패: {resp.text[:200]}")
            data = resp.json()
        return ConfirmResult(
            provider_tx_id=data.get("aid", sid),
            amount_krw=int((data.get("amount") or {}).get("total", amount_krw)),
            method="kakao_pay",
            receipt_url=None,
            raw=data,
            billing_sid=sid,
        )

    async def inactivate_subscription(self, sid: str) -> dict[str, Any]:
        """SID 폐기 — 정기결제 해지 (이후 자동청구 불가)."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.BASE}/manage/subscription/inactive",
                headers=self._headers(),
                data={"cid": self.subscription_cid, "sid": sid},
            )
            if resp.status_code >= 400:
                raise PaymentError(f"카카오 정기해지 실패: {resp.text[:200]}")
            return resp.json()

    async def refund(
        self,
        provider_tx_id: str,
        amount_krw: int,
        reason: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.BASE}/cancel",
                headers=self._headers(),
                data={
                    "cid": self.cid,
                    "tid": provider_tx_id,
                    "cancel_amount": amount_krw,
                    "cancel_tax_free_amount": 0,
                },
            )
            if resp.status_code >= 400:
                raise PaymentError(f"카카오 환불 실패: {resp.text[:200]}")
            return resp.json()


class MockPaymentAdapter:
    """테스트/개발용 — 항상 성공."""

    name = "mock"

    async def create_checkout(
        self,
        amount_krw: int,
        order_name: str,
        order_id: str,
        success_url: str,
        fail_url: str,
        recurring: bool = False,
    ) -> CheckoutSession:
        return CheckoutSession(
            provider="mock",
            redirect_url=f"{success_url}?orderId={order_id}&mockSuccess=true",
            provider_session_id=f"mock_{order_id}",
        )

    async def confirm(
        self,
        provider_session_id: str,
        amount_krw: int,
        extra: dict[str, Any] | None = None,
    ) -> ConfirmResult:
        recurring = bool((extra or {}).get("recurring"))
        return ConfirmResult(
            provider_tx_id=f"mock_tx_{provider_session_id}",
            amount_krw=amount_krw,
            method="mock_card",
            receipt_url=None,
            raw={"mock": True, "extra": extra or {}},
            billing_sid=f"mock_sid_{provider_session_id}" if recurring else None,
        )

    async def pay_subscription(
        self,
        sid: str,
        amount_krw: int,
        order_name: str,
        order_id: str,
        user_id: str,
    ) -> ConfirmResult:
        return ConfirmResult(
            provider_tx_id=f"mock_tx_{order_id}",
            amount_krw=amount_krw,
            method="mock_card",
            receipt_url=None,
            raw={"mock": True, "sid": sid},
            billing_sid=sid,
        )

    async def inactivate_subscription(self, sid: str) -> dict[str, Any]:
        return {"mock": True, "inactivated_sid": sid}

    async def refund(
        self,
        provider_tx_id: str,
        amount_krw: int,
        reason: str,
    ) -> dict[str, Any]:
        return {"mock": True, "refunded": amount_krw, "reason": reason}


def get_adapter(provider: str) -> PaymentAdapter:
    """환경변수 키 기반 어댑터 팩토리. 키 없으면 MockPaymentAdapter."""
    if provider == "toss":
        key = os.environ.get("TOSS_SECRET_KEY")
        return TossPaymentAdapter(key) if key else MockPaymentAdapter()
    if provider == "kakao":
        key = os.environ.get("KAKAO_PAY_ADMIN_KEY")
        cid = os.environ.get("KAKAO_PAY_CID", "TC0ONETIME")
        sub_cid = os.environ.get("KAKAO_PAY_CID_SUBSCRIPTION", "TCSUBSCRIP")
        return KakaoPayAdapter(key, cid, sub_cid) if key else MockPaymentAdapter()
    if provider == "mock":
        return MockPaymentAdapter()
    raise PaymentError(f"지원하지 않는 결제 게이트웨이: {provider}")


# ── 도메인 로직 ──────────────────────────────────────────
async def create_checkout(
    user_id: int,
    plan: str,
    provider: str,
    success_url: str,
    fail_url: str,
    channel: str = "direct",
    tm_partner_code: str | None = None,
    recurring: bool = False,
) -> dict[str, Any]:
    """결제 의도 생성 + 게이트웨이 세션 발급.

    recurring=True 이면 정기결제(자동청구) — 사용자가 명시적으로 정기구독을 선택한
    것이므로 autorenew=True(opt-in) 로 설정한다(BM v2 다크패턴 가드 충족).
    카카오페이는 첫 승인 시 SID 가 발급되어 2회차부터 자동청구된다.

    Returns:
        {payment_id, subscription_id, redirect_url, provider_session_id, recurring}
    """
    _db_required()
    price = validate_plan(plan)
    adapter = get_adapter(provider)

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import (
        Payment,
        PaymentStatus,
        Subscription,
        SubscriptionStatus,
    )

    session: AsyncSession
    async with _session_factory()() as session:
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status=SubscriptionStatus.PENDING,
            channel=channel,
            tm_partner_code=tm_partner_code,
            price_krw=price,
            # 정기구독 선택 = 자동갱신 명시적 opt-in
            autorenew=recurring,
            autorenew_optin_at=datetime.now(UTC) if recurring else None,
        )
        session.add(sub)
        await session.flush()  # sub.id 확보

        payment = Payment(
            subscription_id=sub.id,
            user_id=user_id,
            amount_krw=price,
            status=PaymentStatus.PENDING,
            provider=adapter.name,
        )
        session.add(payment)
        await session.flush()

        order_id = f"jp_{sub.id}_{payment.id}"
        order_name = f"자평 {plan.upper()} 플랜"

        checkout = await adapter.create_checkout(
            amount_krw=price,
            order_name=order_name,
            order_id=order_id,
            success_url=success_url,
            fail_url=fail_url,
            recurring=recurring,
        )

        # provider session id 보관 (confirm 시 조회용)
        payment.provider_tx_id = checkout.provider_session_id
        await session.commit()

        return {
            "payment_id": payment.id,
            "subscription_id": sub.id,
            "order_id": order_id,
            "redirect_url": checkout.redirect_url,
            "provider": adapter.name,
            "provider_session_id": checkout.provider_session_id,
            "recurring": recurring,
        }


async def confirm_payment(
    payment_id: int,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """결제 confirm — 게이트웨이 검증 + 구독 활성화."""
    _db_required()

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import (
        Payment,
        PaymentStatus,
        Subscription,
        SubscriptionStatus,
    )

    session: AsyncSession
    async with _session_factory()() as session:
        payment = await session.get(Payment, payment_id)
        if payment is None:
            raise PaymentError(f"payment {payment_id} 없음")
        if payment.status == PaymentStatus.SUCCEEDED:
            return {"payment_id": payment_id, "status": "already_succeeded"}
        if payment.status != PaymentStatus.PENDING:
            raise PaymentError(f"payment status invalid: {payment.status}")

        sub = await session.get(Subscription, payment.subscription_id)
        recurring = bool(sub and sub.autorenew)

        # 정기 CID 로 승인 + SID 추출을 위해 어댑터에 recurring 컨텍스트 전달
        confirm_extra = {**(extra or {}), "recurring": recurring}

        adapter = get_adapter(payment.provider)
        result = await adapter.confirm(
            provider_session_id=payment.provider_tx_id or "",
            amount_krw=payment.amount_krw,
            extra=confirm_extra,
        )

        # 금액 위변조 차단
        if result.amount_krw != payment.amount_krw:
            payment.status = PaymentStatus.FAILED
            await session.commit()
            raise PaymentError(
                f"금액 불일치: 요청 {payment.amount_krw} vs 결제 {result.amount_krw}",
            )

        now = datetime.now(UTC)
        payment.status = PaymentStatus.SUCCEEDED
        payment.paid_at = now
        payment.provider_tx_id = result.provider_tx_id
        payment.method = result.method
        payment.receipt_url = result.receipt_url

        if sub:
            sub.status = SubscriptionStatus.ACTIVE
            sub.started_at = now
            sub.current_period_end = now + timedelta(days=30)
            # 정기결제 SID 저장 (2회차부터 자동청구 키)
            if result.billing_sid:
                sub.kakao_sid = result.billing_sid

        await session.commit()
        return {
            "payment_id": payment_id,
            "subscription_id": payment.subscription_id,
            "status": "succeeded",
            "amount_krw": payment.amount_krw,
            "provider_tx_id": result.provider_tx_id,
            "receipt_url": result.receipt_url,
        }


async def refund_payment(
    payment_id: int,
    reason: str,
    amount_krw: int | None = None,
) -> dict[str, Any]:
    """환불 — 게이트웨이 호출 + payment 상태 갱신."""
    _db_required()

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import (
        Payment,
        PaymentStatus,
        Subscription,
        SubscriptionStatus,
    )

    session: AsyncSession
    async with _session_factory()() as session:
        payment = await session.get(Payment, payment_id)
        if payment is None:
            raise PaymentError(f"payment {payment_id} 없음")
        if payment.status not in (PaymentStatus.SUCCEEDED, PaymentStatus.PARTIALLY_REFUNDED):
            raise PaymentError(f"환불 불가 상태: {payment.status}")

        refund_amount = amount_krw if amount_krw is not None else (
            payment.amount_krw - payment.refund_amount_krw
        )
        if refund_amount <= 0:
            raise PaymentError("환불 금액은 0보다 커야 합니다.")
        if refund_amount > payment.amount_krw - payment.refund_amount_krw:
            raise PaymentError("이미 환불된 금액을 초과")

        adapter = get_adapter(payment.provider)
        await adapter.refund(payment.provider_tx_id or "", refund_amount, reason)

        now = datetime.now(UTC)
        payment.refund_amount_krw += refund_amount
        payment.refunded_at = now
        if payment.refund_amount_krw >= payment.amount_krw:
            payment.status = PaymentStatus.REFUNDED
            sub = await session.get(Subscription, payment.subscription_id)
            if sub:
                sub.status = SubscriptionStatus.REFUNDED
                sub.canceled_at = now
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED

        await session.commit()
        return {
            "payment_id": payment_id,
            "refund_amount_krw": refund_amount,
            "total_refunded_krw": payment.refund_amount_krw,
            "status": payment.status,
        }


async def set_autorenew(subscription_id: int, enabled: bool) -> bool:
    """자동갱신 opt-in/out — BM v2 가드."""
    _db_required()

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import Subscription

    session: AsyncSession
    async with _session_factory()() as session:
        sub = await session.get(Subscription, subscription_id)
        if sub is None:
            return False
        sub.autorenew = enabled
        sub.autorenew_optin_at = datetime.now(UTC) if enabled else None
        await session.commit()
        return True


async def charge_recurring_subscription(subscription_id: int) -> dict[str, Any]:
    """정기결제 자동청구 (2회차 이후) — 저장된 SID 로 사용자 인증 없이 청구.

    갱신 cron 이 만료 임박 + autorenew + SID 보유 구독을 대상으로 호출한다.
    성공 시 새 Payment(SUCCEEDED) 생성 + current_period_end 30일 연장.
    """
    _db_required()

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import (
        Payment,
        PaymentStatus,
        Subscription,
        SubscriptionStatus,
    )

    session: AsyncSession
    async with _session_factory()() as session:
        sub = await session.get(Subscription, subscription_id)
        if sub is None:
            raise PaymentError(f"subscription {subscription_id} 없음")
        if not sub.autorenew:
            raise PaymentError("자동갱신이 꺼진 구독은 자동청구할 수 없습니다.")
        if sub.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED):
            raise PaymentError(f"자동청구 불가 상태: {sub.status}")
        if not sub.kakao_sid:
            raise PaymentError("정기결제 SID 가 없어 자동청구할 수 없습니다.")

        price = validate_plan(sub.plan)
        payment = Payment(
            subscription_id=sub.id,
            user_id=sub.user_id,
            amount_krw=price,
            status=PaymentStatus.PENDING,
            provider="kakao",
        )
        session.add(payment)
        await session.flush()

        order_id = f"jp_{sub.id}_{payment.id}"
        order_name = f"자평 {sub.plan.upper()} 플랜 (정기)"

        adapter = get_adapter("kakao")
        try:
            result = await adapter.pay_subscription(  # type: ignore[union-attr]
                sid=sub.kakao_sid,
                amount_krw=price,
                order_name=order_name,
                order_id=order_id,
                user_id=str(sub.user_id),
            )
        except PaymentError:
            payment.status = PaymentStatus.FAILED
            await session.commit()
            raise

        now = datetime.now(UTC)
        payment.status = PaymentStatus.SUCCEEDED
        payment.paid_at = now
        payment.provider_tx_id = result.provider_tx_id
        payment.method = result.method

        # 만료일 기준 연장 (이미 지났으면 now 기준)
        base = sub.current_period_end if (
            sub.current_period_end and sub.current_period_end > now
        ) else now
        sub.current_period_end = base + timedelta(days=30)
        sub.status = SubscriptionStatus.ACTIVE

        await session.commit()
        return {
            "subscription_id": sub.id,
            "payment_id": payment.id,
            "amount_krw": price,
            "status": "succeeded",
            "current_period_end": sub.current_period_end.isoformat(),
        }


async def cancel_recurring(subscription_id: int, reason: str = "user_request") -> dict[str, Any]:
    """정기결제 해지 — 카카오 SID 폐기 + autorenew OFF.

    구독은 만료일(current_period_end)까지 유지되고 이후 자동청구되지 않는다(CANCELED).
    """
    _db_required()

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import Subscription, SubscriptionStatus

    session: AsyncSession
    async with _session_factory()() as session:
        sub = await session.get(Subscription, subscription_id)
        if sub is None:
            raise PaymentError(f"subscription {subscription_id} 없음")

        if sub.kakao_sid:
            adapter = get_adapter("kakao")
            await adapter.inactivate_subscription(sub.kakao_sid)  # type: ignore[union-attr]

        now = datetime.now(UTC)
        sub.autorenew = False
        sub.autorenew_optin_at = None
        sub.kakao_sid = None
        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = now

        await session.commit()
        return {
            "subscription_id": sub.id,
            "status": "canceled",
            "reason": reason,
            "access_until": sub.current_period_end.isoformat()
            if sub.current_period_end else None,
        }

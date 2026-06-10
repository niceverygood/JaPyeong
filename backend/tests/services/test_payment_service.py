"""payment_service — 어댑터 + 도메인 단위 테스트.

- PLAN_PRICES 검증
- Mock 어댑터 round-trip (실제 DB 없이 가능)
- 환경변수 기반 adapter 선택
- DB 미설정 시 raise
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from src.services.payment_service import (
    PLAN_PRICES,
    KakaoPayAdapter,
    MockPaymentAdapter,
    PaymentError,
    TossPaymentAdapter,
    cancel_recurring,
    charge_recurring_subscription,
    confirm_payment,
    create_checkout,
    get_adapter,
    refund_payment,
    set_autorenew,
    validate_plan,
)


# ── 가격표 ────────────────────────────────────────────
def test_plan_prices_bm_v2() -> None:
    """월 정기결제 가격: 연회비 ÷ 12 (카카오페이 연 단위 입점 불가 대응)."""
    assert PLAN_PRICES["basic"] == 4_083       # 연 49,000
    assert PLAN_PRICES["standard"] == 12_417   # 연 149,000
    assert PLAN_PRICES["premium"] == 32_500    # 연 390,000
    assert PLAN_PRICES["family"] == 49_167     # 연 590,000


def test_validate_plan_ok() -> None:
    assert validate_plan("premium") == 32_500


def test_validate_plan_unknown() -> None:
    with pytest.raises(PaymentError, match="알 수 없는 plan"):
        validate_plan("vip")


# ── 어댑터 선택 ───────────────────────────────────────
def test_get_adapter_toss_with_key() -> None:
    with patch.dict(os.environ, {"TOSS_SECRET_KEY": "tk_test_xxx"}, clear=False):
        adapter = get_adapter("toss")
    assert isinstance(adapter, TossPaymentAdapter)


def test_get_adapter_toss_no_key_falls_back_to_mock() -> None:
    with patch.dict(os.environ, {}, clear=True):
        adapter = get_adapter("toss")
    assert isinstance(adapter, MockPaymentAdapter)


def test_get_adapter_kakao_with_key() -> None:
    with patch.dict(os.environ, {"KAKAO_PAY_ADMIN_KEY": "kk_admin"}, clear=False):
        adapter = get_adapter("kakao")
    assert isinstance(adapter, KakaoPayAdapter)


def test_get_adapter_mock() -> None:
    assert isinstance(get_adapter("mock"), MockPaymentAdapter)


def test_get_adapter_invalid() -> None:
    with pytest.raises(PaymentError, match="지원하지 않는"):
        get_adapter("naver")


# ── Mock 어댑터 동작 ──────────────────────────────────
async def test_mock_checkout() -> None:
    adapter = MockPaymentAdapter()
    s = await adapter.create_checkout(
        amount_krw=390_000,
        order_name="자평 PREMIUM",
        order_id="jp_1_2",
        success_url="https://x.com/ok",
        fail_url="https://x.com/fail",
    )
    assert s.provider == "mock"
    assert "mockSuccess=true" in s.redirect_url
    assert s.provider_session_id.startswith("mock_jp_")


async def test_mock_confirm() -> None:
    adapter = MockPaymentAdapter()
    r = await adapter.confirm(provider_session_id="mock_xx", amount_krw=100_000)
    assert r.amount_krw == 100_000
    assert r.method == "mock_card"
    assert r.raw["mock"]


async def test_mock_refund() -> None:
    adapter = MockPaymentAdapter()
    r = await adapter.refund("mock_tx_1", 50_000, "고객 요청")
    assert r["refunded"] == 50_000


# ── 도메인: DB 의존 분기 ──────────────────────────────
async def test_create_checkout_requires_db() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(PaymentError, match="DATABASE_URL"):
            await create_checkout(
                user_id=1, plan="premium", provider="mock",
                success_url="https://x.com/ok", fail_url="https://x.com/fail",
            )


async def test_confirm_requires_db() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(PaymentError, match="DATABASE_URL"):
            await confirm_payment(1)


async def test_refund_requires_db() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(PaymentError, match="DATABASE_URL"):
            await refund_payment(1, "이유")


async def test_set_autorenew_requires_db() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(PaymentError, match="DATABASE_URL"):
            await set_autorenew(1, True)


# ── Toss 어댑터 confirm 검증 ───────────────────────────
async def test_toss_confirm_requires_payment_key() -> None:
    adapter = TossPaymentAdapter(secret_key="tk_test")
    with pytest.raises(PaymentError, match="paymentKey"):
        await adapter.confirm(provider_session_id="x", amount_krw=100)


async def test_toss_confirm_http_error() -> None:
    """4xx → PaymentError."""
    import httpx
    adapter = TossPaymentAdapter(secret_key="tk_test")
    mock_resp = httpx.Response(
        400,
        text='{"code":"INVALID_REQUEST"}',
        request=httpx.Request("POST", "https://api.tosspayments.com/v1/payments/confirm"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)):
        with pytest.raises(PaymentError, match="토스 confirm 실패"):
            await adapter.confirm(
                provider_session_id="ord_1",
                amount_krw=100_000,
                extra={"paymentKey": "pk_test_xxx"},
            )


async def test_toss_confirm_success() -> None:
    import httpx
    adapter = TossPaymentAdapter(secret_key="tk_test")
    mock_resp = httpx.Response(
        200,
        json={
            "paymentKey": "pk_real",
            "totalAmount": 100_000,
            "method": "카드",
            "receipt": {"url": "https://receipt.toss/abc"},
        },
        request=httpx.Request("POST", "https://api.tosspayments.com/v1/payments/confirm"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)):
        r = await adapter.confirm(
            provider_session_id="ord_1",
            amount_krw=100_000,
            extra={"paymentKey": "pk_real"},
        )
    assert r.provider_tx_id == "pk_real"
    assert r.amount_krw == 100_000
    assert r.method == "카드"
    assert r.receipt_url == "https://receipt.toss/abc"


# ── Kakao 어댑터 ──────────────────────────────────────
async def test_kakao_confirm_requires_pg_token() -> None:
    adapter = KakaoPayAdapter(admin_key="kk_test")
    with pytest.raises(PaymentError, match="pg_token"):
        await adapter.confirm(provider_session_id="T1", amount_krw=100)


async def test_kakao_ready_success() -> None:
    import httpx
    adapter = KakaoPayAdapter(admin_key="kk_test")
    mock_resp = httpx.Response(
        200,
        json={"tid": "T1234", "next_redirect_pc_url": "https://pay.kakao/redirect"},
        request=httpx.Request("POST", "https://kapi.kakao.com/v1/payment/ready"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)):
        s = await adapter.create_checkout(
            amount_krw=49_000,
            order_name="자평 BASIC",
            order_id="jp_1_1",
            success_url="https://x.com/ok",
            fail_url="https://x.com/fail",
        )
    assert s.provider == "kakao"
    assert s.provider_session_id == "T1234"
    assert s.redirect_url == "https://pay.kakao/redirect"


# ── Kakao 정기결제(subscription) ──────────────────────────
def test_get_adapter_kakao_reads_subscription_cid() -> None:
    with patch.dict(
        os.environ,
        {
            "KAKAO_PAY_ADMIN_KEY": "kk_admin",
            "KAKAO_PAY_CID": "TC0ONETIME",
            "KAKAO_PAY_CID_SUBSCRIPTION": "CT_SUB_REAL",
        },
        clear=False,
    ):
        adapter = get_adapter("kakao")
    assert isinstance(adapter, KakaoPayAdapter)
    assert adapter.subscription_cid == "CT_SUB_REAL"


async def test_kakao_recurring_checkout_uses_subscription_cid() -> None:
    import httpx
    adapter = KakaoPayAdapter(admin_key="kk", cid="TC0ONETIME", subscription_cid="CT_SUB")
    mock_resp = httpx.Response(
        200,
        json={"tid": "T1", "next_redirect_pc_url": "https://pay.kakao/r"},
        request=httpx.Request("POST", "https://kapi.kakao.com/v1/payment/ready"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)) as post:
        await adapter.create_checkout(
            amount_krw=49_000, order_name="자평", order_id="jp_1_1",
            success_url="https://x/ok", fail_url="https://x/no", recurring=True,
        )
    assert post.call_args.kwargs["data"]["cid"] == "CT_SUB"


async def test_kakao_confirm_extracts_sid_when_recurring() -> None:
    import httpx
    adapter = KakaoPayAdapter(admin_key="kk", subscription_cid="CT_SUB")
    mock_resp = httpx.Response(
        200,
        json={"aid": "A1", "sid": "SID_ABC", "amount": {"total": 49_000}},
        request=httpx.Request("POST", "https://kapi.kakao.com/v1/payment/approve"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)) as post:
        r = await adapter.confirm(
            provider_session_id="T1", amount_krw=49_000,
            extra={"pg_token": "pg", "recurring": True},
        )
    assert post.call_args.kwargs["data"]["cid"] == "CT_SUB"
    assert r.billing_sid == "SID_ABC"
    assert r.amount_krw == 49_000


async def test_kakao_pay_subscription_charges_with_sid() -> None:
    import httpx
    adapter = KakaoPayAdapter(admin_key="kk", subscription_cid="CT_SUB")
    mock_resp = httpx.Response(
        200,
        json={"aid": "A2", "amount": {"total": 49_000}},
        request=httpx.Request("POST", "https://kapi.kakao.com/v1/payment/subscription"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)) as post:
        r = await adapter.pay_subscription(
            sid="SID_ABC", amount_krw=49_000, order_name="자평",
            order_id="jp_1_2", user_id="1",
        )
    data = post.call_args.kwargs["data"]
    assert data["sid"] == "SID_ABC"
    assert data["cid"] == "CT_SUB"
    assert r.provider_tx_id == "A2"
    assert r.billing_sid == "SID_ABC"


async def test_kakao_pay_subscription_http_error() -> None:
    import httpx
    adapter = KakaoPayAdapter(admin_key="kk")
    mock_resp = httpx.Response(
        400, text='{"code":-9798}',
        request=httpx.Request("POST", "https://kapi.kakao.com/v1/payment/subscription"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)):
        with pytest.raises(PaymentError, match="정기청구 실패"):
            await adapter.pay_subscription(
                sid="SID", amount_krw=49_000, order_name="자평",
                order_id="jp_1_2", user_id="1",
            )


async def test_kakao_inactivate_subscription() -> None:
    import httpx
    adapter = KakaoPayAdapter(admin_key="kk", subscription_cid="CT_SUB")
    mock_resp = httpx.Response(
        200,
        json={"sid": "SID_ABC", "status": "INACTIVE"},
        request=httpx.Request(
            "POST", "https://kapi.kakao.com/v1/payment/manage/subscription/inactive",
        ),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)) as post:
        out = await adapter.inactivate_subscription("SID_ABC")
    assert post.call_args.kwargs["data"] == {"cid": "CT_SUB", "sid": "SID_ABC"}
    assert out["status"] == "INACTIVE"


async def test_mock_recurring_confirm_returns_sid() -> None:
    adapter = MockPaymentAdapter()
    r = await adapter.confirm("mock_T1", 49_000, extra={"recurring": True})
    assert r.billing_sid == "mock_sid_mock_T1"
    r2 = await adapter.confirm("mock_T1", 49_000, extra={})
    assert r2.billing_sid is None


# ── 정기결제 도메인: DB 의존 분기 ─────────────────────────
async def test_charge_recurring_requires_db() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(PaymentError, match="DATABASE_URL"):
            await charge_recurring_subscription(1)


async def test_cancel_recurring_requires_db() -> None:
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(PaymentError, match="DATABASE_URL"):
            await cancel_recurring(1)

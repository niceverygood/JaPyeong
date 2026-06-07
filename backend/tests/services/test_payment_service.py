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
    confirm_payment,
    create_checkout,
    get_adapter,
    refund_payment,
    set_autorenew,
    validate_plan,
)


# ── 가격표 ────────────────────────────────────────────
def test_plan_prices_bm_v2() -> None:
    """BM v2 가격: 49k / 149k / 390k / 590k."""
    assert PLAN_PRICES["basic"] == 49_000
    assert PLAN_PRICES["standard"] == 149_000
    assert PLAN_PRICES["premium"] == 390_000
    assert PLAN_PRICES["family"] == 590_000


def test_validate_plan_ok() -> None:
    assert validate_plan("premium") == 390_000


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

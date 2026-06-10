"""결제 라우터 — checkout / confirm / refund / autorenew.

엔드포인트:
  POST   /api/v1/payment/checkout         결제 의도 생성 (recurring=True 면 정기결제)
  POST   /api/v1/payment/confirm          결제 검증·구독 활성화 (정기 시 SID 저장)
  POST   /api/v1/payment/refund           환불
  PATCH  /api/v1/payment/autorenew        자동갱신 opt-in/out
  POST   /api/v1/payment/recurring/cancel 정기결제 해지 (SID 폐기)
  GET    /api/v1/payment/plans            BM v2 가격표 조회 (공개)
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from src.api.dependencies import get_current_user_id
from src.services.payment_service import (
    PLAN_PRICES,
    PaymentError,
    cancel_recurring,
    confirm_payment,
    create_checkout,
    refund_payment,
    set_autorenew,
    verify_iap_purchase,
)

router = APIRouter(prefix="/payment", tags=["payment"])


class CheckoutRequest(BaseModel):
    plan: Literal["basic", "standard", "premium", "family"]
    provider: Literal["toss", "kakao", "mock"]
    success_url: HttpUrl
    fail_url: HttpUrl
    channel: str = Field(default="direct", max_length=32)
    tm_partner_code: str | None = Field(default=None, max_length=40)
    # 정기결제(자동청구) 여부 — 카카오페이 SID 발급. 선택 = 자동갱신 opt-in.
    recurring: bool = False


class CheckoutResponse(BaseModel):
    payment_id: int
    subscription_id: int
    order_id: str
    redirect_url: str
    provider: str
    provider_session_id: str
    recurring: bool = False


class ConfirmRequest(BaseModel):
    payment_id: int
    extra: dict[str, Any] = Field(default_factory=dict)
    # 토스: {paymentKey: ...}
    # 카카오: {pg_token: ...}


class ConfirmResponse(BaseModel):
    payment_id: int
    subscription_id: int | None = None
    status: str
    amount_krw: int | None = None
    provider_tx_id: str | None = None
    receipt_url: str | None = None


class RefundRequest(BaseModel):
    payment_id: int
    reason: str = Field(min_length=1, max_length=200)
    amount_krw: int | None = Field(default=None, ge=1)


class AutorenewRequest(BaseModel):
    subscription_id: int
    enabled: bool


class CancelRecurringRequest(BaseModel):
    subscription_id: int
    reason: str = Field(default="user_request", max_length=200)


@router.get("/plans")
async def list_plans() -> dict[str, dict[str, Any]]:
    """공개 가격표 — BM v2."""
    descriptions = {
        "basic":    {"label": "Basic",    "monthly": True,
                     "description": "사주 분석 + 일진 알림"},
        "standard": {"label": "Standard", "monthly": True,
                     "description": "AI 상담 + 결정 도우미"},
        "premium":  {"label": "Premium",  "monthly": True,
                     "description": "자문위원 1:1 + 우선 매칭"},
        "family":   {"label": "Family",   "monthly": True,
                     "description": "최대 5명 + 가족 궁합"},
    }
    return {
        plan: {"price_krw": PLAN_PRICES[plan], **descriptions[plan]}
        for plan in PLAN_PRICES
    }


@router.post("/checkout", response_model=CheckoutResponse, status_code=201)
async def checkout_endpoint(
    body: CheckoutRequest,
    user_id: int = Depends(get_current_user_id),
) -> CheckoutResponse:
    try:
        result = await create_checkout(
            user_id=user_id,
            plan=body.plan,
            provider=body.provider,
            success_url=str(body.success_url),
            fail_url=str(body.fail_url),
            channel=body.channel,
            tm_partner_code=body.tm_partner_code,
            recurring=body.recurring,
        )
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return CheckoutResponse(**result)


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_endpoint(
    body: ConfirmRequest,
    user_id: int = Depends(get_current_user_id),
) -> ConfirmResponse:
    try:
        result = await confirm_payment(body.payment_id, extra=body.extra)
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ConfirmResponse(**result)


class IapVerifyRequest(BaseModel):
    platform: Literal["ios", "android"]
    plan: Literal["basic", "standard", "premium", "family"]
    product_id: str = Field(min_length=1, max_length=120)
    receipt: str = Field(min_length=1)  # iOS: base64 영수증 / Android: purchaseToken
    transaction_id: str | None = Field(default=None, max_length=120)
    package_name: str | None = Field(default=None, max_length=120)


@router.post("/iap/verify", response_model=ConfirmResponse)
async def iap_verify_endpoint(
    body: IapVerifyRequest,
    user_id: int = Depends(get_current_user_id),
) -> ConfirmResponse:
    """네이티브 인앱결제(App Store / Play) 영수증 검증 + 구독 활성화."""
    try:
        result = await verify_iap_purchase(
            user_id=user_id,
            platform=body.platform,
            plan=body.plan,
            product_id=body.product_id,
            receipt=body.receipt,
            transaction_id=body.transaction_id,
            package_name=body.package_name,
        )
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ConfirmResponse(**result)


@router.post("/refund")
async def refund_endpoint(
    body: RefundRequest,
    user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
    try:
        return await refund_payment(
            body.payment_id,
            reason=body.reason,
            amount_krw=body.amount_krw,
        )
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/autorenew")
async def autorenew_endpoint(
    body: AutorenewRequest,
    user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
    """자동갱신 opt-in/out — BM v2: 디폴트 OFF, 사용자 명시적 의사 필요."""
    ok = await set_autorenew(body.subscription_id, body.enabled)
    if not ok:
        raise HTTPException(status_code=404, detail="구독을 찾을 수 없습니다.")
    return {"subscription_id": body.subscription_id, "autorenew": body.enabled}


@router.post("/recurring/cancel")
async def cancel_recurring_endpoint(
    body: CancelRecurringRequest,
    user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
    """정기결제 해지 — 카카오 SID 폐기 + 자동갱신 OFF.

    구독은 current_period_end 까지 유지되고 이후 자동청구되지 않는다.
    """
    try:
        return await cancel_recurring(body.subscription_id, reason=body.reason)
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

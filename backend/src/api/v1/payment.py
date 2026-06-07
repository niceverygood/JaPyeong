"""결제 라우터 — checkout / confirm / refund / autorenew.

엔드포인트:
  POST   /api/v1/payment/checkout       결제 의도 생성
  POST   /api/v1/payment/confirm        결제 검증·구독 활성화
  POST   /api/v1/payment/refund         환불
  PATCH  /api/v1/payment/autorenew      자동갱신 opt-in/out
  GET    /api/v1/payment/plans          BM v2 가격표 조회 (공개)
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from src.api.dependencies import get_current_user_id
from src.services.payment_service import (
    PLAN_PRICES,
    PaymentError,
    confirm_payment,
    create_checkout,
    refund_payment,
    set_autorenew,
)

router = APIRouter(prefix="/payment", tags=["payment"])


class CheckoutRequest(BaseModel):
    plan: Literal["basic", "standard", "premium", "family"]
    provider: Literal["toss", "kakao", "mock"]
    success_url: HttpUrl
    fail_url: HttpUrl
    channel: str = Field(default="direct", max_length=32)
    tm_partner_code: str | None = Field(default=None, max_length=40)


class CheckoutResponse(BaseModel):
    payment_id: int
    subscription_id: int
    order_id: str
    redirect_url: str
    provider: str
    provider_session_id: str


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

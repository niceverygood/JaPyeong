"""/v1/coins 라우터 — 선충전 지갑 + 고마진 단건 상품 (ARPU 엔진).

엔드포인트:
  GET  /v1/coins/balance        잔액 조회
  GET  /v1/coins/products       카탈로그(충전팩 + 단건 상품)
  POST /v1/coins/charge/verify  소비성 IAP 영수증 검증 → 코인 적립(멱등=transaction_id)
  POST /v1/coins/spend          단건 상품 코인 차감 → 프리미엄(opus) 콘텐츠 생성
  GET  /v1/coins/ledger         최근 거래 원장

단건은 '코인 차감 → 콘텐츠 생성' 순. 생성 실패 시 차감을 환원(refund)한다.
충전 검증은 transaction_id 를 멱등 키로 사용해 영수증 재전송에도 2번 적립되지 않는다.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.ai import consultation, guardrails
from src.ai.glossary import annotate_hanja
from src.ai.tone_down import tone_down
from src.api.dependencies import get_current_user_id
from src.engine.schema import BirthInfo
from src.middleware.rate_limit import get_limiter
from src.services import coin_service, payment_service, saju_service
from src.services.coin_catalog import CHARGE_PACKS, SPEND_ITEMS, get_charge_pack, get_spend_item

router = APIRouter(prefix="/v1/coins", tags=["coins"])


def _post(text: str) -> str:
    return annotate_hanja(tone_down(text))


# ── 스키마 ───────────────────────────────────────────────
class ChargeVerifyRequest(BaseModel):
    platform: Literal["ios", "android"]
    product_id: str = Field(min_length=1, max_length=60)   # 충전팩 코드(= IAP product_id)
    receipt: str = Field(min_length=1)
    # 멱등 키의 핵심 — 누락 시 같은 팩 재구매가 중복으로 묻혀 코인 미적립됨. 필수.
    transaction_id: str = Field(min_length=1, max_length=160)
    package_name: str | None = Field(default=None, max_length=120)


class BalanceResponse(BaseModel):
    balance: int


class ChargeResponse(BaseModel):
    balance: int
    credited: int
    duplicate: bool = False


class OptionIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


class CoinSpendRequest(BaseModel):
    item_code: str = Field(min_length=1, max_length=40)
    birth: BirthInfo
    question: str | None = Field(default=None, max_length=2000)
    option_a: OptionIn | None = None
    option_b: OptionIn | None = None
    context: str | None = Field(default=None, max_length=2000)
    # 클라이언트가 1회 액션마다 발급하는 멱등 키 — 재시도 시 중복 차감 방지.
    idempotency_key: str | None = Field(default=None, max_length=120)


class CoinSpendResponse(BaseModel):
    item_code: str
    balance: int
    charged: int
    content: dict[str, Any]


# ── 카탈로그 ─────────────────────────────────────────────
@router.get("/products")
async def products() -> dict[str, Any]:
    """충전팩 + 단건 상품 카탈로그 (공개)."""
    return {
        "charge_packs": [
            {
                "code": p.code, "price_krw": p.price_krw, "coins": p.coins,
                "bonus": p.bonus, "total_coins": p.total_coins, "label": p.label,
            }
            for p in CHARGE_PACKS.values()
        ],
        "spend_items": [
            {
                "code": s.code, "cost": s.cost, "label": s.label,
                "kind": s.kind, "description": s.description,
            }
            for s in SPEND_ITEMS.values()
        ],
    }


@router.get("/balance", response_model=BalanceResponse)
async def balance(user_id: int = Depends(get_current_user_id)) -> BalanceResponse:
    try:
        bal = await coin_service.get_balance(user_id)
    except coin_service.CoinDatabaseUnavailable as e:
        raise HTTPException(503, "코인 기능을 일시적으로 사용할 수 없습니다.") from e
    return BalanceResponse(balance=bal)


@router.get("/ledger")
async def ledger_endpoint(
    limit: int = 50, user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
    try:
        rows = await coin_service.ledger(user_id, limit=limit)
    except coin_service.CoinDatabaseUnavailable as e:
        raise HTTPException(503, "코인 기능을 일시적으로 사용할 수 없습니다.") from e
    return {"transactions": rows}


# ── 충전 (소비성 IAP) ────────────────────────────────────
@router.post("/charge/verify", response_model=ChargeResponse)
async def charge_verify(
    body: ChargeVerifyRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
) -> ChargeResponse:
    """스토어 소비성 결제 영수증 검증 → 코인 적립. transaction_id 멱등."""
    await get_limiter().enforce_ip_only(request)
    pack = get_charge_pack(body.product_id)
    if pack is None:
        raise HTTPException(400, f"알 수 없는 충전 상품: {body.product_id}")
    try:
        verified = await payment_service.verify_consumable(
            platform=body.platform,
            product_id=body.product_id,
            receipt=body.receipt,
            transaction_id=body.transaction_id,
            package_name=body.package_name,
        )
    except payment_service.PaymentError as e:
        raise HTTPException(400, str(e)) from e

    idem = f"charge:{body.platform}:{verified['transaction_id']}"
    try:
        result = await coin_service.charge(
            user_id=user_id,
            coins=pack.coins,
            bonus=pack.bonus,
            idempotency_key=idem,
            memo=f"충전 {pack.label}",
        )
    except coin_service.CoinDatabaseUnavailable as e:
        raise HTTPException(503, "코인 적립을 일시적으로 처리할 수 없습니다.") from e
    return ChargeResponse(
        balance=result["balance"], credited=result["credited"],
        duplicate=result["duplicate"],
    )


# ── 단건 사용 (차감 → 프리미엄 콘텐츠) ───────────────────────
def _serialize(result, *, decision: bool = False) -> dict[str, Any]:  # noqa: ANN001
    base: dict[str, Any] = {
        "answer": _post(result.answer),
        "basis": _post(result.basis),
        "perspective": _post(result.perspective),
        "timing": _post(result.timing),
        "cautions": [_post(c) for c in result.cautions],
        "citations": [
            {"source": _post(c.source), "volume": _post(c.volume) if c.volume else None}
            for c in result.citations
        ],
        "contested": [_post(c) for c in result.contested],
        "confidence": result.confidence,
        "model": result.model,
    }
    if decision:
        base.update(
            option_a_view=_post(result.option_a_view),
            option_b_view=_post(result.option_b_view),
            comparison=_post(result.comparison),
            lean=result.lean,
            lean_reason=_post(result.lean_reason),
        )
    return base


_SAJU_DEEP_Q = (
    "내 사주 명식을 정밀하게 풀이해 주세요. 일간의 강약, 격국, 용신, 십성 구성과 "
    "대운의 큰 흐름을 근거와 고전 인용과 함께 깊이 있게 설명해 주세요."
)
_REPORT_Q = (
    "2026년 한 해와 다가오는 대운의 흐름을 종합 리포트로 정리해 주세요. "
    "직업·재물·관계·건강 영역별로 좋은 시기와 주의할 시기를 근거와 함께 구체적으로."
)


@router.post("/spend", response_model=CoinSpendResponse)
async def spend(
    body: CoinSpendRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
) -> CoinSpendResponse:
    """단건 상품 — 프리미엄(opus) 콘텐츠를 먼저 생성한 뒤 성공 시에만 코인을 차감한다.

    설계(generate-then-charge): 생성 실패는 차감 자체가 일어나지 않으므로 환불 경로가
    필요 없다(환불-실패-무시 같은 정합성 위험 제거). 차감 전 잔액을 확인해 무료 생성도 막는다.
    """
    await get_limiter().enforce_ip_only(request)
    item = get_spend_item(body.item_code)
    if item is None:
        raise HTTPException(400, f"알 수 없는 단건 상품: {body.item_code}")

    # 0. 위기 키워드 가드 (질문/맥락) — 무엇보다 먼저, 차감/생성 없이 안전 안내
    crisis_blob = " ".join(
        s for s in (body.question or "", body.context or "",
                    body.option_a.description if body.option_a else "",
                    body.option_b.description if body.option_b else "") if s
    )
    if crisis_blob.strip():
        pre = guardrails.check_question(crisis_blob)
        if not pre.safe:
            bal = await coin_service.get_balance(user_id)
            return CoinSpendResponse(
                item_code=item.code, balance=bal, charged=0,
                content={"answer": pre.answer, "basis": "안전 안내",
                         "confidence": "high", "model": "(guardrail)", "flags": list(pre.flags)},
            )

    # 1. 결정론 명식 + 필수 payload 검증 (생성/차감 전)
    try:
        natal = saju_service.analyze_natal(body.birth).model_dump()
    except NotImplementedError as e:
        raise HTTPException(422, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if item.kind == "consult" and not (body.question and body.question.strip()):
        raise HTTPException(400, "질문(question)이 필요합니다.")
    if item.kind == "decision" and not (body.option_a and body.option_b):
        raise HTTPException(400, "두 선택지(option_a, option_b)가 필요합니다.")

    # 2. 잔액 사전 확인 — 부족하면 생성도 하지 않음(무료 생성 방지)
    try:
        if await coin_service.get_balance(user_id) < item.cost:
            raise HTTPException(
                402, f"코인이 부족합니다. (필요 {item.cost})",
            )
    except coin_service.CoinDatabaseUnavailable as e:
        raise HTTPException(503, "코인 기능을 일시적으로 사용할 수 없습니다.") from e

    # 3. 프리미엄 콘텐츠 생성 (실패해도 차감 없음 → 환불 불필요)
    try:
        if item.kind == "decision":
            result = consultation.consult_decision(
                natal=natal,
                option_a_title=body.option_a.title,    # type: ignore[union-attr]
                option_a_desc=body.option_a.description,  # type: ignore[union-attr]
                option_b_title=body.option_b.title,    # type: ignore[union-attr]
                option_b_desc=body.option_b.description,  # type: ignore[union-attr]
                context=body.context,
                user_tier="premium",
            )
            content = _serialize(result, decision=True)
        else:
            q = (
                body.question if item.kind == "consult"
                else _SAJU_DEEP_Q if item.kind == "saju_deep"
                else _REPORT_Q
            )
            result = consultation.consult(
                natal=natal, question=q or _SAJU_DEEP_Q, user_tier="premium",
            )
            post = guardrails.filter_answer(result.answer)
            content = _serialize(result)
            content["answer"] = _post(post.answer)
            content["flags"] = list(post.flags)
    except Exception as e:  # noqa: BLE001 — 생성 실패: 차감 전이므로 그대로 502
        raise HTTPException(502, f"콘텐츠 생성에 실패했습니다: {e}") from e

    # 4. 생성 성공 → 코인 차감 (멱등). 동시 차감 경합으로 잔액이 빠진 드문 경우엔
    #    이미 생성된 콘텐츠를 반환하되 charged=0 으로 표기(과금 안전 우선).
    try:
        deb = await coin_service.spend(
            user_id, item.code, item.cost,
            idempotency_key=(f"spend:{user_id}:{body.idempotency_key}"
                             if body.idempotency_key else None),
            memo=item.label,
        )
        balance, charged = deb["balance"], deb["charged"]
    except coin_service.InsufficientCoins:
        balance, charged = await coin_service.get_balance(user_id), 0
    except coin_service.CoinDatabaseUnavailable as e:
        raise HTTPException(503, "코인 기능을 일시적으로 사용할 수 없습니다.") from e

    return CoinSpendResponse(
        item_code=item.code, balance=balance, charged=charged, content=content,
    )

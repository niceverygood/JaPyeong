"""Vercel Python 서버리스 진입점.

웹앱과 같은 도메인의 /api/* 로 룰베이스 사주 엔진 + LLM 자문 + 사전예약을 노출한다.
무거운 의존(DB·Redis)은 import하지 않는다.
"""

import os
import sys

# 저장소의 backend/ 를 import 경로에 추가 (vercel.json functions.includeFiles로 번들됨)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import json  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402

import httpx  # noqa: E402
from fastapi import FastAPI, Header, HTTPException  # noqa: E402
from pydantic import BaseModel, EmailStr, Field  # noqa: E402

from src.api.v1 import (  # noqa: E402
    auth,
    chat,
    compatibility,
    date_selection,
    decision,
    notifications,
    payment,
    saju,
    timing,
)

app = FastAPI(title="자평(子平) API", version="0.0.1")

# 라우터 prefix(/v1/...) → /api/v1/...
app.include_router(saju.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(compatibility.router, prefix="/api")
app.include_router(date_selection.router, prefix="/api")
app.include_router(decision.router, prefix="/api")
app.include_router(timing.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
# 회원·결제 — main.py 와 동일하게 /api/v1 prefix (라우터 자체 prefix 는 /auth, /payment)
# DB import 는 서비스 함수 내부에서 lazy 하게 발생하므로 cold start 부담 없음.
app.include_router(auth.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "japyeong", "env": "vercel"}


@app.get("/api/_status")
async def feature_status() -> dict:
    """활성 기능 노출 — 어떤 자격증명이 들어왔는지 한눈에."""
    return {
        "saju_engine": True,  # 항상 활성 (룰베이스)
        "ai_chat": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
        "preorder_webhook": bool(os.environ.get("PREORDER_WEBHOOK_URL")),
        "database": bool(os.environ.get("DATABASE_URL")),
        "payment_portone": bool(
            os.environ.get("PORTONE_API_SECRET") and os.environ.get("PORTONE_STORE_ID")
        ),
        "payment_kakao": bool(os.environ.get("KAKAO_PAY_ADMIN_KEY")),
        "notes": [
            "saju_engine: 룰베이스 + 잠정 strength/geokguk/yongsin",
            "ai_chat: ANTHROPIC_API_KEY 설정 시 활성",
            "openrouter: OPENROUTER_API_KEY 설정 시 /api/_admin/cross-check 가용",
            "database: DATABASE_URL 설정 + alembic 마이그레이션 후 활성",
        ],
    }


# ── 관리자 전용 다중 LLM 교차검증 ────────────────────────────
@app.post("/api/_admin/cross-check")
async def admin_cross_check(
    n: int = 3,
    authorization: str = Header(default=""),
) -> dict:
    """결정론적 합성 사주 n건 × 다계열 LLM 교차검증.

    인증: 헤더 `Authorization: Bearer <OPENROUTER_API_KEY>` 가 env 값과 일치.
    cost·time 한계로 n은 [1, 5] 클램프 (Vercel 60s 타임아웃 보호).

    ⚠ LLM 합의는 자문위원 검증을 대체하지 않는다. 통설 영역 보조 신호.
    """
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise HTTPException(503, "OPENROUTER_API_KEY 미설정")
    expected = f"Bearer {key}"
    if authorization != expected:
        raise HTTPException(401, "관리자 인증 실패")

    # lazy import — cold start 시 httpx 외 추가 import 없음
    from src.services.llm_crosscheck import (
        generate_seeded_cases,
        report_to_dict,
        run_crosscheck,
    )

    n = max(1, min(n, 5))
    cases = generate_seeded_cases(n)
    report = await run_crosscheck(cases, api_key=key)
    return report_to_dict(report)


# ── 사전예약 수집 ──────────────────────────────────────────────
class PreorderRequest(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=80)
    plan: str = Field(default="undecided", pattern=r"^(standard|premium|pro|undecided)$")
    source: str | None = Field(default=None, max_length=40)


class PreorderResponse(BaseModel):
    ok: bool


@app.post("/api/preorder", response_model=PreorderResponse)
async def preorder(req: PreorderRequest) -> PreorderResponse:
    """사전예약 수집.

    Vercel 함수 로그에 구조화 JSON으로 기록(필수). PREORDER_WEBHOOK_URL 환경변수가
    설정되어 있으면 동일 페이로드를 POST(예: Slack/Make/Apps Script). 실패해도
    사용자 응답은 200 — 로그는 항상 남는다.
    """
    payload = {
        "type": "preorder",
        "email": req.email,
        "name": (req.name or "").strip() or None,
        "plan": req.plan,
        "source": req.source,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    # 1. Vercel 로그(구조화) — 필수
    print(json.dumps({"event": "japyeong.preorder", **payload}, ensure_ascii=False))

    # 2. 옵션 웹훅(설정된 경우만)
    webhook = os.environ.get("PREORDER_WEBHOOK_URL")
    if webhook and re.match(r"^https?://", webhook):
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                await client.post(webhook, json=payload)
        except Exception as e:  # 절대 실패 금지 (로그는 이미 남았다)
            print(json.dumps({"event": "japyeong.preorder.webhook_err", "err": str(e)}))

    return PreorderResponse(ok=True)

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
from fastapi import FastAPI  # noqa: E402
from pydantic import BaseModel, EmailStr, Field  # noqa: E402

from src.api.v1 import chat, saju  # noqa: E402

app = FastAPI(title="자평(子平) API", version="0.0.1")

# 라우터 prefix(/v1/saju, /v1/chat) → /api/v1/...
app.include_router(saju.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "japyeong", "env": "vercel"}


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

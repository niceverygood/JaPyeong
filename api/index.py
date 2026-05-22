"""Vercel Python 서버리스 진입점.

웹앱과 같은 도메인의 /api/* 로 룰베이스 사주 엔진을 노출한다(동일 출처 → CORS 불필요).
무거운 의존(DB·Redis·LLM)은 import하지 않는다 — 사주 분석 경로만 노출.
"""

import os
import sys

# 저장소의 backend/ 를 import 경로에 추가 (vercel.json functions.includeFiles로 번들됨)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi import FastAPI  # noqa: E402

from src.api.v1 import saju  # noqa: E402

app = FastAPI(title="자평(子平) API", version="0.0.1")

# saju.router prefix = /v1/saju → /api/v1/saju/...
app.include_router(saju.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "japyeong", "env": "vercel"}

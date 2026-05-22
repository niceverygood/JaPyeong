"""FastAPI 진입점.

Phase 0: 헬스체크만. API 라우터는 Phase 2에서 src/api/v1 하위로 추가.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.api.v1 import saju
from src.core.config import get_settings
from src.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("japyeong.startup", env=settings.env)
    yield
    log.info("japyeong.shutdown")


app = FastAPI(
    title="자평(子平) API",
    version="0.0.1",
    description="명리학 AI 자문 SaaS 백엔드",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """루트는 API 문서(Swagger)로 안내."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "japyeong", "env": settings.env}


app.include_router(saju.router)

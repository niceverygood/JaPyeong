"""관리자 전용 — 결정 로그 익명 export + 집계 리포트.

인증: ADMIN_BEARER_TOKEN 정적 토큰 (FastAPI dependency get_admin_user_id)

엔드포인트:
  GET /api/v1/admin/decisions/export?format=jsonl|csv&since=YYYY-MM-DD&type=career
  GET /api/v1/admin/decisions/aggregate?since=YYYY-MM-DD&min_count=50
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.api.dependencies import get_admin_user_id
from src.services.decision_export_service import (
    aggregation_report,
    export_decisions_csv,
    export_decisions_jsonl,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _parse_since(since: str | None) -> datetime | None:
    if not since:
        return None
    try:
        # YYYY-MM-DD
        return datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail="since 는 YYYY-MM-DD 형식이어야 합니다.",
        ) from e


@router.get("/decisions/export")
async def export_decisions(
    fmt: Literal["jsonl", "csv"] = Query(default="jsonl", alias="format"),
    since: str | None = Query(default=None, description="YYYY-MM-DD (default: 90일전)"),
    decision_type: str | None = Query(default=None, alias="type"),
    limit: int = Query(default=10_000, ge=1, le=100_000),
    _admin: int = Depends(get_admin_user_id),
) -> Response:
    """익명 결정 로그 export.

    JSONL: line-delimited JSON, 스트리밍 친화.
    CSV: BOM 포함 (Excel 호환).
    """
    since_dt = _parse_since(since)

    if fmt == "jsonl":
        body = await export_decisions_jsonl(since_dt, decision_type, limit)
        return Response(
            content=body,
            media_type="application/x-ndjson",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="decisions_{datetime.now(UTC):%Y%m%d}.jsonl"'
                ),
            },
        )
    # csv
    body = await export_decisions_csv(since_dt, decision_type, limit)
    # Excel 호환 — UTF-8 BOM
    csv_bytes = "﻿".encode() + body.encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="decisions_{datetime.now(UTC):%Y%m%d}.csv"'
            ),
        },
    )


@router.get("/decisions/aggregate")
async def aggregate_decisions(
    since: str | None = Query(default=None, description="YYYY-MM-DD"),
    min_count: int = Query(default=50, ge=1, le=10_000),
    _admin: int = Depends(get_admin_user_id),
) -> dict:
    """집계 리포트 — decision_type × lean 평균 만족도.

    50건 미만 버킷은 응답에서 제외 (default min_count).
    """
    since_dt = _parse_since(since)
    buckets = await aggregation_report(since_dt, min_count=min_count)
    return {
        "since": since_dt.isoformat() if since_dt else None,
        "min_count": min_count,
        "bucket_count": len(buckets),
        "buckets": [
            {
                "decision_type": b.decision_type,
                "lean": b.lean,
                "count": b.count,
                "avg_satisfaction_3m": b.avg_satisfaction_3m,
                "avg_satisfaction_6m": b.avg_satisfaction_6m,
            }
            for b in buckets
        ],
    }

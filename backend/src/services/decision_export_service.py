"""결정 로그 익명 export — 해자 ❶ 데이터 자산화.

목적:
  - B2B 임원 코칭·연구기관·내부 분석용 익명 JSONL/CSV
  - PII (name/birth_place/exact birth datetime) 절대 미포함
  - sajupillars_anon (이미 익명화된 8자/일간/격국/용신) + decision_type +
    lean/confidence/actual_choice/만족도 점수만 export

PII 제거 정책:
  - user_id → 결정적 hash (k-anonymity 보장 안함, 단순 cross-join 차단용)
  - birth_record_id → drop
  - PII 메모 필드 (option_a_summary, option_b_summary, user_context,
    advisor_response_summary) → drop (자유 텍스트라 PII 노출 위험)

집계:
  decision_type × confidence × lean × satisfaction_bucket

관리자 인증 필수 (X-API-Token: ADMIN_BEARER_TOKEN).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass(slots=True, frozen=True)
class AnonymizedDecisionRow:
    """익명화된 1건의 결정 로그."""

    user_hash: str
    decision_type: str
    saju_summary: dict[str, Any]  # ilgan, gyeokguk, yongsin, etc.
    lean: str | None
    confidence: str | None
    actual_choice: str | None
    actual_at_days: int | None    # created_at 으로부터의 days (날짜 자체 X)
    satisfaction_3m: int | None
    satisfaction_6m: int | None
    decided_year_month: str       # "2026-06" — created_at 의 연월


def _user_hash(user_id: int) -> str:
    """user_id → 결정적 hash (12자, hex). cross-export join 차단용."""
    salt = os.environ.get("EXPORT_HASH_SALT", "japyeong-export-v1")
    h = hashlib.sha256(f"{salt}:{user_id}".encode())
    return h.hexdigest()[:12]


def _saju_summary(sajupillars_anon: dict[str, Any]) -> dict[str, Any]:
    """원본 sajupillars_anon 에서 익명·집계용 키만 골라냄.

    저장된 dict 가 어떤 키든 갖고 있을 수 있으니 whitelist 방식.
    """
    if not isinstance(sajupillars_anon, dict):
        return {}
    keys = ("ilgan", "gyeokguk", "yongsin", "year_pillar",
            "month_pillar", "day_pillar", "hour_pillar")
    return {k: sajupillars_anon[k] for k in keys if k in sajupillars_anon}


def anonymize_row(decision_log: Any) -> AnonymizedDecisionRow:  # noqa: ANN401
    """DB DecisionLog → 익명 행."""
    created = decision_log.created_at
    actual_at = decision_log.actual_choice_at
    actual_days = None
    if actual_at and created:
        actual_days = (actual_at - created).days

    return AnonymizedDecisionRow(
        user_hash=_user_hash(decision_log.user_id),
        decision_type=decision_log.decision_type,
        saju_summary=_saju_summary(decision_log.sajupillars_anon),
        lean=decision_log.lean,
        confidence=decision_log.confidence,
        actual_choice=decision_log.actual_choice,
        actual_at_days=actual_days,
        satisfaction_3m=decision_log.followup_3m_satisfaction,
        satisfaction_6m=decision_log.followup_6m_satisfaction,
        decided_year_month=created.strftime("%Y-%m") if created else "",
    )


def row_to_jsonl(row: AnonymizedDecisionRow) -> str:
    """행 → JSONL 한 줄 (개행 포함)."""
    return json.dumps(
        {
            "user_hash": row.user_hash,
            "decision_type": row.decision_type,
            "saju": row.saju_summary,
            "lean": row.lean,
            "confidence": row.confidence,
            "actual_choice": row.actual_choice,
            "actual_at_days": row.actual_at_days,
            "satisfaction_3m": row.satisfaction_3m,
            "satisfaction_6m": row.satisfaction_6m,
            "decided_ym": row.decided_year_month,
        },
        ensure_ascii=False,
    ) + "\n"


def rows_to_csv(rows: list[AnonymizedDecisionRow]) -> str:
    """행 목록 → CSV (saju_summary 는 키 평탄화)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "user_hash", "decision_type", "ilgan", "gyeokguk", "yongsin",
        "lean", "confidence", "actual_choice", "actual_at_days",
        "satisfaction_3m", "satisfaction_6m", "decided_ym",
    ])
    for r in rows:
        s = r.saju_summary
        writer.writerow([
            r.user_hash, r.decision_type,
            s.get("ilgan", ""), s.get("gyeokguk", ""), s.get("yongsin", ""),
            r.lean or "", r.confidence or "", r.actual_choice or "",
            r.actual_at_days if r.actual_at_days is not None else "",
            r.satisfaction_3m if r.satisfaction_3m is not None else "",
            r.satisfaction_6m if r.satisfaction_6m is not None else "",
            r.decided_year_month,
        ])
    return buf.getvalue()


# ── 집계 ──────────────────────────────────────────────
@dataclass(slots=True, frozen=True)
class AggregationBucket:
    """decision_type × lean × satisfaction_bucket 집계."""

    decision_type: str
    lean: str | None
    count: int
    avg_satisfaction_3m: float | None
    avg_satisfaction_6m: float | None


def _safe_avg(values: list[int]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def aggregate(rows: list[AnonymizedDecisionRow]) -> list[AggregationBucket]:
    """결정 유형 × 자평 권유 방향 별 평균 만족도.

    1만 건 누적 시 의미 있는 신호. 50건 미만 버킷은 통계 부정확 — 호출자가 필터.
    """
    buckets: dict[tuple[str, str | None], dict[str, list[int]]] = {}
    for row in rows:
        key = (row.decision_type, row.lean)
        bucket = buckets.setdefault(key, {"3m": [], "6m": []})
        if row.satisfaction_3m is not None:
            bucket["3m"].append(row.satisfaction_3m)
        if row.satisfaction_6m is not None:
            bucket["6m"].append(row.satisfaction_6m)

    out: list[AggregationBucket] = []
    for (dt, lean), bucket in sorted(buckets.items()):
        # count 는 lean 별 전체 row 수 — 만족도 응답 없는 행도 포함
        count = sum(1 for r in rows if r.decision_type == dt and r.lean == lean)
        out.append(AggregationBucket(
            decision_type=dt,
            lean=lean,
            count=count,
            avg_satisfaction_3m=_safe_avg(bucket["3m"]),
            avg_satisfaction_6m=_safe_avg(bucket["6m"]),
        ))
    return out


# ── DB Wrapper ────────────────────────────────────────
def _db_enabled() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


async def fetch_decisions_since(
    since: datetime | None = None,
    decision_type: str | None = None,
    limit: int = 10_000,
) -> list[Any]:
    """DB에서 결정 로그 조회. since=None → 최근 90일."""
    if not _db_enabled():
        return []

    if since is None:
        since = datetime.now(UTC) - timedelta(days=90)

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import DecisionLog

    session: AsyncSession
    async with _session_factory()() as session:
        stmt = (
            select(DecisionLog)
            .where(DecisionLog.created_at >= since)
            .order_by(DecisionLog.created_at.desc())
            .limit(limit)
        )
        if decision_type:
            stmt = stmt.where(DecisionLog.decision_type == decision_type)
        rows = (await session.execute(stmt)).scalars().all()
        return list(rows)


async def export_decisions_jsonl(
    since: datetime | None = None,
    decision_type: str | None = None,
    limit: int = 10_000,
) -> str:
    """JSONL 문자열 — 익명화된 전체."""
    rows = await fetch_decisions_since(since, decision_type, limit)
    anon = [anonymize_row(r) for r in rows]
    return "".join(row_to_jsonl(r) for r in anon)


async def export_decisions_csv(
    since: datetime | None = None,
    decision_type: str | None = None,
    limit: int = 10_000,
) -> str:
    """CSV 문자열 — 익명화된 전체."""
    rows = await fetch_decisions_since(since, decision_type, limit)
    anon = [anonymize_row(r) for r in rows]
    return rows_to_csv(anon)


async def aggregation_report(
    since: datetime | None = None,
    min_count: int = 50,
) -> list[AggregationBucket]:
    """집계 리포트 — 50건 미만 버킷 제외 (통계 신뢰도)."""
    rows = await fetch_decisions_since(since, limit=100_000)
    anon = [anonymize_row(r) for r in rows]
    buckets = aggregate(anon)
    return [b for b in buckets if b.count >= min_count]

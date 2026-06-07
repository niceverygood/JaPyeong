"""결정 추적 데이터셋 자산화 — 진짜 해자 ❶.

사용자가 입력한 결정 + 자평 자문 → DecisionLog 에 익명화 저장.
3개월 / 6개월 후 만족도 follow-up 스케줄러가 사용.

원칙:
  - PII (이름·연락처) 분리: birth_record 식별자만 저장
  - 사주 8자는 그대로 (익명 통계 가능, 본인 식별은 birth_record_id 거쳐야 함)
  - follow-up due_at 자동 설정 (created_at + 90d / + 180d)
  - DATABASE_URL 미설정 시 무동작 (현재 운영 상태)

집계 가능:
  - 격국·일주별 결정 만족도 (1만 건+ 시 패턴 도출)
  - 자문 lean 정확도 (사후 actual_choice vs lean 비교)
  - 결정 유형별 평균 만족도
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any


# ── DB 활성 여부 ─────────────────────────────────────────
def _db_enabled() -> bool:
    """DATABASE_URL 환경변수가 있어야만 DB 저장 시도."""
    return bool(os.environ.get("DATABASE_URL"))


# ── 사주 익명화 ──────────────────────────────────────────
def anonymize_natal(natal_pillars: dict[str, Any]) -> dict[str, Any]:
    """birth_record 의 평문 PII 제거. 사주 8자 + 일간 + 격국·용신만 유지.

    [입력] natal_pillars (예: {"pillars": {"year": {"gan": "甲", "ji": "子"}, ...}})
    [출력] {"pillars": {...}, "day_master": "丙", "ten_gods": {...}, ...}
            PII (name, birth_place 등) 일체 없음.

    decision_log.sajupillars_anon 컬럼에 그대로 저장.
    """
    # 사주 4기둥만 추출
    pillars = natal_pillars.get("pillars", {})
    out: dict[str, Any] = {"pillars": pillars}

    # 일간·오행·격국·용신 등 메타데이터는 보존 (집계용)
    for key in (
        "day_master", "day_master_element", "ten_gods", "five_elements",
        "geokguk", "yongsin", "strength",
    ):
        if key in natal_pillars:
            v = natal_pillars[key]
            # 객체면 그대로 (이미 JSON-serializable)
            if isinstance(v, dict):
                out[key] = v
            else:
                out[key] = str(v) if v is not None else None

    return out


# ── 저장 (DB 활성 시) ────────────────────────────────────
async def save_decision_log(
    user_id: int | None,
    birth_record_id: int | None,
    decision_type: str,
    natal: dict[str, Any],
    option_a_summary: str | None,
    option_b_summary: str | None,
    user_context: str | None,
    lean: str | None,
    advisor_response_summary: str | None,
    confidence: str | None,
) -> int | None:
    """결정 로그 저장. 저장된 row id 반환 (DB 비활성 시 None).

    user_id / birth_record_id 가 None 이면 (회원 미가입 상태) 저장하지 않음.
    Sprint 1-2 회원·결제 활성 후부터 실 저장 시작.
    """
    if not _db_enabled():
        return None
    if user_id is None or birth_record_id is None:
        return None

    # 지연 import — DB 미설정 환경에서 import 비용 회피
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import DecisionLog

    now = datetime.now(UTC)
    row = DecisionLog(
        user_id=user_id,
        birth_record_id=birth_record_id,
        decision_type=decision_type,
        sajupillars_anon=anonymize_natal(natal),
        option_a_summary=option_a_summary,
        option_b_summary=option_b_summary,
        user_context=user_context,
        lean=lean,
        advisor_response_summary=advisor_response_summary,
        confidence=confidence,
        # follow-up 자동 스케줄 (3개월 / 6개월 후)
        followup_3m_due_at=now + timedelta(days=90),
        followup_6m_due_at=now + timedelta(days=180),
    )

    session: AsyncSession
    async with _session_factory()() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row.id


# ── follow-up cron 핸들러 ─────────────────────────────────
async def list_due_followups(window: str = "3m") -> list[dict[str, Any]]:
    """due_at 이 지난 follow-up 대상 조회.

    Args:
        window: "3m" 또는 "6m"

    Returns:
        [{decision_id, user_id, created_at, decision_type, ...}, ...]

    호출자: 매일 새벽 cron 으로 실행 → 카톡/이메일 발송 (Sprint 9-10)
    """
    if not _db_enabled():
        return []

    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import DecisionLog

    now = datetime.now(UTC)
    if window == "3m":
        due_col = DecisionLog.followup_3m_due_at
        sent_col = DecisionLog.followup_3m_sent_at
    elif window == "6m":
        due_col = DecisionLog.followup_6m_due_at
        sent_col = DecisionLog.followup_6m_sent_at
    else:
        raise ValueError(f"window must be '3m' or '6m', got {window!r}")

    session: AsyncSession
    async with _session_factory()() as session:
        stmt = select(DecisionLog).where(
            and_(due_col.is_not(None), due_col <= now, sent_col.is_(None)),
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "decision_id": r.id,
                "user_id": r.user_id,
                "created_at": r.created_at,
                "decision_type": r.decision_type,
                "lean": r.lean,
                "window": window,
            }
            for r in rows
        ]


# ── follow-up 응답 기록 ───────────────────────────────────
async def record_followup_response(
    decision_id: int,
    window: str,
    satisfaction_score: int,
    actual_choice: str | None = None,
) -> bool:
    """사용자 follow-up 응답 기록.

    Returns: True 성공 / False (DB 비활성 또는 미존재)
    """
    if not _db_enabled():
        return False
    if not (1 <= satisfaction_score <= 10):
        raise ValueError(f"satisfaction_score must be 1..10, got {satisfaction_score}")

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import DecisionLog

    now = datetime.now(UTC)
    session: AsyncSession
    async with _session_factory()() as session:
        row = await session.get(DecisionLog, decision_id)
        if row is None:
            return False
        if window == "3m":
            row.followup_3m_sent_at = now
            row.followup_3m_satisfaction = satisfaction_score
        elif window == "6m":
            row.followup_6m_sent_at = now
            row.followup_6m_satisfaction = satisfaction_score
        else:
            raise ValueError(f"window must be '3m' or '6m', got {window!r}")
        if actual_choice and not row.actual_choice:
            row.actual_choice = actual_choice
            row.actual_choice_at = now
        await session.commit()
        return True


# ── 집계 (관리자 분석용) ──────────────────────────────────
def aggregate_satisfaction_by_decision_type(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """결정 유형별 평균 만족도.

    입력은 보통 list_due_followups 결과 또는 별도 쿼리 결과.
    DB 의존 없는 순수 함수 — 테스트·집계 자유.
    """
    by_type: dict[str, list[int]] = {}
    for r in rows:
        s = r.get("satisfaction_score")
        t = r.get("decision_type")
        if s is None or t is None:
            continue
        by_type.setdefault(t, []).append(int(s))

    out: dict[str, dict[str, float]] = {}
    for t, scores in by_type.items():
        out[t] = {
            "count": len(scores),
            "avg": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
        }
    return out

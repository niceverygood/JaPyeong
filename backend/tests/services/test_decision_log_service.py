"""services.decision_log_service 단위 테스트.

DB 미설정 환경 (현재 운영) + DB 설정 환경 양쪽 동작 검증.
DB 실 연결 테스트는 별도 통합 테스트로 분리.
"""

from __future__ import annotations

import os

import pytest

from src.services.decision_log_service import (
    aggregate_satisfaction_by_decision_type,
    anonymize_natal,
    list_due_followups,
    record_followup_response,
    save_decision_log,
)


# ── anonymize_natal — 순수 함수, DB 무관 ─────────────────
def test_anonymize_natal_keeps_pillars() -> None:
    natal = {
        "pillars": {
            "year": {"gan": "甲", "ji": "子"},
            "month": {"gan": "丙", "ji": "寅"},
            "day": {"gan": "丁", "ji": "巳"},
            "hour": {"gan": "戊", "ji": "戌"},
        },
        "day_master": "丁",
        "day_master_element": "火",
        "geokguk": {"name": "정관격", "ten_god": "정관"},
        "yongsin": {"yongsin": "水", "huishin": "金"},
    }
    out = anonymize_natal(natal)
    assert out["pillars"] == natal["pillars"]
    assert out["day_master"] == "丁"
    assert out["geokguk"]["name"] == "정관격"
    assert out["yongsin"]["yongsin"] == "水"


def test_anonymize_natal_drops_pii() -> None:
    """name·birth_place·user_id 같은 PII 는 결과에 없어야 함."""
    natal = {
        "pillars": {"year": {"gan": "甲", "ji": "子"}},
        "name": "홍길동",       # PII
        "birth_place": "서울",  # PII
        "user_id": 12345,       # PII
    }
    out = anonymize_natal(natal)
    assert "name" not in out
    assert "birth_place" not in out
    assert "user_id" not in out


def test_anonymize_natal_minimal() -> None:
    """필수 필드만 있는 minimal 입력."""
    out = anonymize_natal({"pillars": {"day": {"gan": "丙", "ji": "午"}}})
    assert out == {"pillars": {"day": {"gan": "丙", "ji": "午"}}}


# ── save_decision_log — DB 없음 시 무동작 ──────────────────
@pytest.mark.asyncio
async def test_save_returns_none_without_db() -> None:
    """DATABASE_URL 미설정 시 None 반환 (저장 시도 X)."""
    # 안전: 환경변수 확실히 제거
    os.environ.pop("DATABASE_URL", None)
    rv = await save_decision_log(
        user_id=1, birth_record_id=1, decision_type="career",
        natal={"pillars": {}},
        option_a_summary="이직", option_b_summary="잔류",
        user_context=None, lean="A",
        advisor_response_summary="흐름이 살짝 A 쪽",
        confidence="medium",
    )
    assert rv is None


@pytest.mark.asyncio
async def test_save_returns_none_without_user_id() -> None:
    """user_id가 None이면 (비회원) 저장 X."""
    os.environ.pop("DATABASE_URL", None)
    rv = await save_decision_log(
        user_id=None, birth_record_id=1, decision_type="career",
        natal={}, option_a_summary=None, option_b_summary=None,
        user_context=None, lean=None,
        advisor_response_summary=None, confidence=None,
    )
    assert rv is None


# ── list_due_followups — DB 없음 시 빈 리스트 ──────────────
@pytest.mark.asyncio
async def test_list_due_followups_empty_without_db() -> None:
    os.environ.pop("DATABASE_URL", None)
    rv = await list_due_followups("3m")
    assert rv == []


@pytest.mark.asyncio
async def test_list_due_followups_invalid_window() -> None:
    """잘못된 window 입력은 ValueError."""
    os.environ["DATABASE_URL"] = "postgresql://x"  # DB 활성 가정
    try:
        with pytest.raises(ValueError):
            await list_due_followups("invalid")  # type: ignore[arg-type]
    finally:
        os.environ.pop("DATABASE_URL", None)


# ── record_followup_response — DB 없음 시 False ──────────
@pytest.mark.asyncio
async def test_record_followup_returns_false_without_db() -> None:
    os.environ.pop("DATABASE_URL", None)
    rv = await record_followup_response(1, "3m", satisfaction_score=8)
    assert rv is False


@pytest.mark.asyncio
async def test_record_followup_validates_score() -> None:
    """1~10 범위 밖 점수는 ValueError. 단, DB 미설정 환경에서는 먼저 False 반환."""
    os.environ.pop("DATABASE_URL", None)
    # DB 비활성 환경에서는 검증 전에 False 반환 (early return)
    assert await record_followup_response(1, "3m", satisfaction_score=11) is False
    # DB 활성 가정 시에만 ValueError 발생
    os.environ["DATABASE_URL"] = "postgresql://x"
    try:
        with pytest.raises(ValueError):
            await record_followup_response(1, "3m", satisfaction_score=11)
        with pytest.raises(ValueError):
            await record_followup_response(1, "3m", satisfaction_score=0)
    finally:
        os.environ.pop("DATABASE_URL", None)


# ── aggregate_satisfaction_by_decision_type — 순수 함수 ─
def test_aggregate_empty() -> None:
    assert aggregate_satisfaction_by_decision_type([]) == {}


def test_aggregate_basic() -> None:
    rows = [
        {"decision_type": "career", "satisfaction_score": 8},
        {"decision_type": "career", "satisfaction_score": 10},
        {"decision_type": "marriage", "satisfaction_score": 7},
        {"decision_type": "marriage", "satisfaction_score": 9},
        {"decision_type": "marriage", "satisfaction_score": 5},
    ]
    out = aggregate_satisfaction_by_decision_type(rows)
    assert out["career"]["count"] == 2
    assert out["career"]["avg"] == 9.0
    assert out["career"]["min"] == 8
    assert out["career"]["max"] == 10
    assert out["marriage"]["count"] == 3
    assert out["marriage"]["avg"] == 7.0


def test_aggregate_skips_missing() -> None:
    """satisfaction_score 가 None 인 row 는 스킵."""
    rows = [
        {"decision_type": "career", "satisfaction_score": 8},
        {"decision_type": "career", "satisfaction_score": None},  # skip
        {"decision_type": None, "satisfaction_score": 5},  # skip
    ]
    out = aggregate_satisfaction_by_decision_type(rows)
    assert out["career"]["count"] == 1
    assert out["career"]["avg"] == 8.0

"""decision_export_service — 익명화 / JSONL / CSV / 집계 단위 테스트."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.services.decision_export_service import (
    AnonymizedDecisionRow,
    _user_hash,
    aggregate,
    anonymize_row,
    export_decisions_csv,
    export_decisions_jsonl,
    row_to_jsonl,
    rows_to_csv,
)


def _decision(
    user_id: int = 1,
    decision_type: str = "career",
    lean: str | None = "A",
    confidence: str | None = "high",
    actual_choice: str | None = None,
    sat_3m: int | None = None,
    sat_6m: int | None = None,
    saju: dict | None = None,
):
    return SimpleNamespace(
        id=1,
        user_id=user_id,
        decision_type=decision_type,
        sajupillars_anon=saju or {"ilgan": "甲", "gyeokguk": "정관격",
                                    "yongsin": "水", "extra": "drop_me"},
        lean=lean,
        confidence=confidence,
        actual_choice=actual_choice,
        actual_choice_at=None if not actual_choice
            else datetime(2026, 6, 15, tzinfo=UTC),  # created + 14d
        followup_3m_satisfaction=sat_3m,
        followup_6m_satisfaction=sat_6m,
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )


# ── user hash ─────────────────────────────────────────
def test_user_hash_deterministic() -> None:
    h1 = _user_hash(42)
    h2 = _user_hash(42)
    assert h1 == h2
    assert len(h1) == 12


def test_user_hash_differs_per_user() -> None:
    assert _user_hash(1) != _user_hash(2)


def test_user_hash_changes_with_salt() -> None:
    with patch.dict(os.environ, {"EXPORT_HASH_SALT": "salt-A"}, clear=False):
        h1 = _user_hash(1)
    with patch.dict(os.environ, {"EXPORT_HASH_SALT": "salt-B"}, clear=False):
        h2 = _user_hash(1)
    assert h1 != h2


# ── anonymize_row ─────────────────────────────────────
def test_anonymize_drops_pii_keys() -> None:
    row = anonymize_row(_decision())
    assert "extra" not in row.saju_summary  # whitelist 만 통과
    assert row.saju_summary == {"ilgan": "甲", "gyeokguk": "정관격", "yongsin": "水"}


def test_anonymize_user_id_replaced_with_hash() -> None:
    row = anonymize_row(_decision(user_id=999))
    assert row.user_hash == _user_hash(999)
    # 평문 user_id 노출 X
    assert "999" not in row.user_hash


def test_anonymize_actual_at_days() -> None:
    row = anonymize_row(_decision(actual_choice="A"))
    assert row.actual_at_days == 14


def test_anonymize_decided_ym() -> None:
    row = anonymize_row(_decision())
    assert row.decided_year_month == "2026-06"


def test_anonymize_saju_summary_handles_non_dict() -> None:
    bad = _decision(saju={})
    bad.sajupillars_anon = "not a dict"  # 비정상 데이터
    row = anonymize_row(bad)
    assert row.saju_summary == {}


# ── JSONL ─────────────────────────────────────────────
def test_row_to_jsonl_format() -> None:
    row = anonymize_row(_decision(sat_3m=8))
    line = row_to_jsonl(row)
    assert line.endswith("\n")
    parsed = json.loads(line)
    assert parsed["decision_type"] == "career"
    assert parsed["satisfaction_3m"] == 8
    assert parsed["saju"]["ilgan"] == "甲"


def test_row_to_jsonl_korean_preserved() -> None:
    row = AnonymizedDecisionRow(
        user_hash="abc", decision_type="결혼", saju_summary={"격국": "정관"},
        lean="A", confidence="high", actual_choice="A",
        actual_at_days=10, satisfaction_3m=8, satisfaction_6m=9,
        decided_year_month="2026-06",
    )
    line = row_to_jsonl(row)
    assert "결혼" in line
    assert "\\u" not in line  # ensure_ascii=False 검증


# ── CSV ───────────────────────────────────────────────
def test_csv_header_row() -> None:
    csv_text = rows_to_csv([anonymize_row(_decision())])
    first_line = csv_text.splitlines()[0]
    assert "user_hash" in first_line
    assert "ilgan" in first_line


def test_csv_handles_empty_rows() -> None:
    csv_text = rows_to_csv([])
    assert csv_text.count("\n") == 1  # 헤더만


# ── aggregate ─────────────────────────────────────────
def test_aggregate_groups_by_type_and_lean() -> None:
    rows = [
        anonymize_row(_decision(decision_type="career", lean="A", sat_3m=8)),
        anonymize_row(_decision(decision_type="career", lean="A", sat_3m=9)),
        anonymize_row(_decision(decision_type="career", lean="B", sat_3m=5)),
        anonymize_row(_decision(decision_type="marriage", lean="A", sat_3m=10)),
    ]
    buckets = aggregate(rows)
    by_key = {(b.decision_type, b.lean): b for b in buckets}

    assert by_key[("career", "A")].count == 2
    assert by_key[("career", "A")].avg_satisfaction_3m == 8.5
    assert by_key[("career", "B")].count == 1
    assert by_key[("marriage", "A")].avg_satisfaction_3m == 10.0


def test_aggregate_handles_no_satisfaction() -> None:
    rows = [anonymize_row(_decision(decision_type="career", lean="A"))]
    buckets = aggregate(rows)
    assert buckets[0].avg_satisfaction_3m is None
    assert buckets[0].avg_satisfaction_6m is None
    assert buckets[0].count == 1


# ── DB 분기 ───────────────────────────────────────────
async def test_export_jsonl_no_db() -> None:
    with patch.dict(os.environ, {}, clear=True):
        result = await export_decisions_jsonl()
    assert result == ""


async def test_export_csv_no_db_has_header_only() -> None:
    with patch.dict(os.environ, {}, clear=True):
        result = await export_decisions_csv()
    assert "user_hash" in result.splitlines()[0]


@pytest.mark.parametrize("since,expect_ok", [
    ("2026-06-01", True),
    ("invalid", False),
])
def test_parse_since_format(since: str, expect_ok: bool) -> None:
    from fastapi import HTTPException

    from src.api.v1.admin import _parse_since

    if expect_ok:
        _parse_since(since)
    else:
        with pytest.raises(HTTPException):
            _parse_since(since)

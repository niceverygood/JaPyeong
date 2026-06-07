"""solapi_service — 마스킹 + 어댑터 선택 + Mock 발송 + 메시지 빌더."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.services.solapi_service import (
    MockSolapiAdapter,
    SolapiHttpAdapter,
    _solapi_signature,
    build_followup_message,
    get_adapter,
    mask_phone,
    send_followup,
)


# ── mask_phone ────────────────────────────────────────
@pytest.mark.parametrize("inp,expected", [
    ("010-1234-5678", "010-XXXX-5678"),
    ("01012345678", "010-XXXX-5678"),
    ("+82 10 1234 5678", "821-XXXX-5678"),
    ("123", "XXX-XXXX"),
    ("", "XXX-XXXX"),
])
def test_mask_phone(inp: str, expected: str) -> None:
    assert mask_phone(inp) == expected


# ── HMAC 서명 ─────────────────────────────────────────
def test_solapi_signature_deterministic() -> None:
    s1 = _solapi_signature("secret", "2026-06-07T10:00:00Z", "salt123")
    s2 = _solapi_signature("secret", "2026-06-07T10:00:00Z", "salt123")
    assert s1 == s2
    assert len(s1) == 64  # SHA-256 hex


def test_solapi_signature_changes_with_secret() -> None:
    s1 = _solapi_signature("secret-A", "d", "s")
    s2 = _solapi_signature("secret-B", "d", "s")
    assert s1 != s2


# ── 어댑터 선택 ──────────────────────────────────────
def test_adapter_mock_when_keys_missing() -> None:
    with patch.dict(os.environ, {}, clear=True):
        assert isinstance(get_adapter(), MockSolapiAdapter)


def test_adapter_http_with_full_env() -> None:
    with patch.dict(os.environ, {
        "SOLAPI_API_KEY": "k",
        "SOLAPI_API_SECRET": "s",
        "SOLAPI_FROM_NUMBER": "0212345678",
    }, clear=False):
        assert isinstance(get_adapter(), SolapiHttpAdapter)


def test_adapter_falls_back_to_mock_when_no_sender() -> None:
    with patch.dict(os.environ, {
        "SOLAPI_API_KEY": "k",
        "SOLAPI_API_SECRET": "s",
    }, clear=True):
        assert isinstance(get_adapter(), MockSolapiAdapter)


# ── Mock 어댑터 발송 ─────────────────────────────────
async def test_mock_alimtalk_success() -> None:
    adapter = MockSolapiAdapter()
    r = await adapter.send_alimtalk("010-1234-5678", "pf", "tpl", {"#{x}": "1"})
    assert r.success
    assert r.channel == "alimtalk"
    assert r.raw["to_masked"] == "010-XXXX-5678"
    # 평문 phone 미저장
    assert "010-1234-5678" not in str(r.raw)


async def test_mock_lms_success() -> None:
    adapter = MockSolapiAdapter()
    r = await adapter.send_lms("010-1111-2222", "test message")
    assert r.success
    assert r.channel == "lms"
    assert "test message".startswith(r.raw["text_preview"])


# ── 메시지 빌더 가드 ──────────────────────────────────
def test_followup_3m_message_no_forbidden_words() -> None:
    msg = build_followup_message(3, "이직")
    # 자평 금지어 사전
    for forbidden in ("100%", "반드시", "놓치면", "운명을 바꾼다", "위기 시기"):
        assert forbidden not in msg, f"금지어 '{forbidden}' 노출"


def test_followup_6m_message_no_forbidden_words() -> None:
    msg = build_followup_message(6, "결혼")
    for forbidden in ("100%", "반드시", "놓치면", "운명을 바꾼다", "위기 시기"):
        assert forbidden not in msg


def test_followup_message_includes_unsubscribe() -> None:
    """수신거부 의무 표기 — 정보통신망법."""
    msg = build_followup_message(3, "이사")
    assert "수신거부" in msg


def test_followup_message_truncates_long_label() -> None:
    """긴 라벨이 메시지 길이 초과시 절단."""
    msg = build_followup_message(3, "x" * 100)
    # label 부분이 20자로 제한
    assert msg.count("x") == 20


# ── send_followup 통합 (Mock) ────────────────────────
async def test_send_followup_uses_lms_when_no_template() -> None:
    """KAKAO_PF_ID/TEMPLATE 없으면 LMS 폴백."""
    with patch.dict(os.environ, {}, clear=True):
        r = await send_followup("010-1234-5678", months=3, decision_label="이직")
    assert r.success
    assert r.channel == "lms"


async def test_send_followup_uses_alimtalk_when_template_set() -> None:
    """KAKAO_PF_ID + template_id 있으면 알림톡 시도."""
    with patch.dict(os.environ, {
        "KAKAO_PF_ID": "pf123",
        "KAKAO_TEMPLATE_FOLLOWUP_3M": "TPL_3M",
    }, clear=False):
        r = await send_followup("010-1234-5678", months=3, decision_label="이직")
    assert r.success
    assert r.channel == "alimtalk"


# ── HTTP 어댑터 ──────────────────────────────────────
async def test_http_adapter_handles_4xx() -> None:
    adapter = SolapiHttpAdapter("k", "s", "0212345678")
    mock_resp = httpx.Response(
        400,
        text="bad",
        request=httpx.Request("POST", "https://api.solapi.com/messages/v4/send"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)):
        r = await adapter.send_lms("010-1234-5678", "hi")
    assert not r.success
    assert r.error and "400" in r.error


async def test_http_adapter_success() -> None:
    adapter = SolapiHttpAdapter("k", "s", "0212345678")
    mock_resp = httpx.Response(
        200,
        json={"statusCode": "2000", "messageId": "MID_xyz"},
        request=httpx.Request("POST", "https://api.solapi.com/messages/v4/send"),
    )
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_resp)):
        r = await adapter.send_alimtalk("010-1234-5678", "pf", "tpl", {})
    assert r.success
    assert r.provider_msg_id == "MID_xyz"

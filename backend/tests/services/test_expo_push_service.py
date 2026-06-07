"""services.expo_push_service 단위 테스트.

httpx mock 으로 실제 네트워크 호출 없이 검증.
"""

from __future__ import annotations

import httpx
import pytest

from src.services.expo_push_service import (
    EXPO_PUSH_URL,
    MAX_BATCH,
    PushMessage,
    _chunk,
    _to_expo_payload,
    is_expo_token,
    send_batch,
)


def msg(token: str = "ExponentPushToken[abc]", title: str = "T", body: str = "B") -> PushMessage:
    return PushMessage(
        to=token, title=title, body=body,
        data={"type": "daily_fortune"},
        channel_id="daily-fortune",
    )


# ── 빈 입력 ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_empty_messages() -> None:
    result = await send_batch([])
    assert result.sent == 0
    assert result.succeeded == 0
    assert result.failed == 0


# ── 토큰 포맷 검증 ────────────────────────────────────────
def test_is_expo_token() -> None:
    assert is_expo_token("ExponentPushToken[xxx]")
    assert is_expo_token("ExponentPushToken[abc123-def]")
    assert not is_expo_token("fcm-raw-token-here")
    assert not is_expo_token("ExpoToken[xxx]")
    assert not is_expo_token("")


# ── payload 변환 ──────────────────────────────────────────
def test_payload_basic() -> None:
    m = PushMessage(to="ExponentPushToken[x]", title="T", body="B")
    p = _to_expo_payload(m)
    assert p == {"to": "ExponentPushToken[x]", "title": "T", "body": "B", "sound": "default"}


def test_payload_with_data_and_channel() -> None:
    m = PushMessage(
        to="ExponentPushToken[x]", title="T", body="B",
        data={"k": "v"}, channel_id="daily-fortune",
    )
    p = _to_expo_payload(m)
    assert p["data"] == {"k": "v"}
    assert p["channelId"] == "daily-fortune"


# ── 청크 분할 (MAX_BATCH = 100) ───────────────────────────
def test_chunk_under_max() -> None:
    items = [msg() for _ in range(50)]
    chunks = _chunk(items, MAX_BATCH)
    assert len(chunks) == 1
    assert len(chunks[0]) == 50


def test_chunk_exact_max() -> None:
    items = [msg() for _ in range(100)]
    chunks = _chunk(items, MAX_BATCH)
    assert len(chunks) == 1


def test_chunk_over_max() -> None:
    items = [msg() for _ in range(250)]
    chunks = _chunk(items, MAX_BATCH)
    assert len(chunks) == 3
    assert [len(c) for c in chunks] == [100, 100, 50]


# ── 성공 응답 처리 ────────────────────────────────────────
@pytest.mark.asyncio
async def test_all_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_post(self, url: str, **kwargs):  # noqa: ARG001
        return httpx.Response(
            200,
            json={"data": [{"status": "ok", "id": "rcpt-1"} for _ in range(3)]},
            request=httpx.Request("POST", EXPO_PUSH_URL),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    messages = [msg(f"ExponentPushToken[t{i}]") for i in range(3)]
    result = await send_batch(messages)
    assert result.sent == 3
    assert result.succeeded == 3
    assert result.failed == 0
    assert result.invalid_tokens == []


# ── DeviceNotRegistered → invalid_tokens 수집 ─────────────
@pytest.mark.asyncio
async def test_device_not_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_post(self, url: str, **kwargs):  # noqa: ARG001
        return httpx.Response(
            200,
            json={"data": [
                {"status": "ok", "id": "rcpt-1"},
                {"status": "error", "message": "expired",
                 "details": {"error": "DeviceNotRegistered"}},
                {"status": "ok", "id": "rcpt-3"},
            ]},
            request=httpx.Request("POST", EXPO_PUSH_URL),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    messages = [
        msg("ExponentPushToken[ok-1]"),
        msg("ExponentPushToken[bad]"),
        msg("ExponentPushToken[ok-2]"),
    ]
    result = await send_batch(messages)
    assert result.succeeded == 2
    assert result.failed == 1
    assert result.invalid_tokens == ["ExponentPushToken[bad]"]


# ── 네트워크 실패 ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_network_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_post(self, url: str, **kwargs):  # noqa: ARG001
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    messages = [msg() for _ in range(5)]
    result = await send_batch(messages)
    assert result.sent == 5
    assert result.succeeded == 0
    assert result.failed == 5


# ── 5xx 에러 ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_post(self, url: str, **kwargs):  # noqa: ARG001
        return httpx.Response(503, json={"errors": [{"message": "service unavailable"}]}, request=httpx.Request("POST", EXPO_PUSH_URL))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    messages = [msg() for _ in range(2)]
    result = await send_batch(messages)
    assert result.failed == 2


# ── 250건 배치 자동 분할 ──────────────────────────────────
@pytest.mark.asyncio
async def test_250_messages_split_to_3_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    async def mock_post(self, url: str, **kwargs):  # noqa: ARG001
        nonlocal call_count
        call_count += 1
        body_size = len(kwargs.get("json", []))
        return httpx.Response(
            200,
            json={"data": [{"status": "ok", "id": f"r{i}"} for i in range(body_size)]},
            request=httpx.Request("POST", EXPO_PUSH_URL),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    messages = [msg(f"ExponentPushToken[t{i}]") for i in range(250)]
    result = await send_batch(messages)
    assert call_count == 3  # 100 + 100 + 50
    assert result.succeeded == 250
    assert result.failed == 0


# ── URL·헤더 정합성 (배치 1건 발송 시) ──────────────────
@pytest.mark.asyncio
async def test_uses_expo_url(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    async def mock_post(self, url: str, **kwargs):  # noqa: ARG001
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        captured["json"] = kwargs.get("json", [])
        return httpx.Response(200, json={"data": [{"status": "ok"}]}, request=httpx.Request("POST", EXPO_PUSH_URL))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    await send_batch([msg()])
    assert captured["url"] == EXPO_PUSH_URL
    assert captured["headers"].get("Content-Type") == "application/json"

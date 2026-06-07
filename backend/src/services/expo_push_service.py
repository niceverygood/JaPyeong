"""Expo Push HTTP 배치 호출 — 일진 알림 발송 인프라.

Expo Push API: https://docs.expo.dev/push-notifications/sending-notifications/
  - 최대 100 messages/요청
  - 무료, 인증 불필요 (단 Receipts 조회는 access token 권장)
  - DeviceNotRegistered 받으면 push_token.is_active = False 처리

자평 가드:
  - body 단정 어휘는 daily_fortune.py 에서 이미 차단
  - 시간대 분산: cron 이 사용자별 발송 시간 (notif_daily_time_hhmm) 기준 호출
  - 실패 시 push_token.last_error 기록 → 운영자 점검

이 모듈은 순수 HTTP 클라이언트 — DB 의존 없음.
DB 통합은 daily_fortune_cron.py 에서.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
MAX_BATCH = 100  # Expo 정책
DEFAULT_TIMEOUT = 30.0

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PushMessage:
    """단일 푸시 메시지 — Expo 포맷에 그대로 매핑."""

    to: str           # Expo push token "ExponentPushToken[xxx]"
    title: str
    body: str
    data: dict[str, Any] | None = None
    channel_id: str | None = None  # Android (예: "daily-fortune")
    sound: str = "default"


@dataclass(frozen=True, slots=True)
class PushSendResult:
    """배치 발송 결과."""

    sent: int                              # 전송 시도 건수
    succeeded: int                         # ok 응답
    failed: int                            # error 응답
    invalid_tokens: list[str]              # DeviceNotRegistered → 토큰 비활성화
    raw_responses: list[dict[str, Any]]    # Expo Receipts (감사·로깅)


def _to_expo_payload(msg: PushMessage) -> dict[str, Any]:
    """PushMessage → Expo JSON payload."""
    payload: dict[str, Any] = {
        "to": msg.to,
        "title": msg.title,
        "body": msg.body,
        "sound": msg.sound,
    }
    if msg.data:
        payload["data"] = msg.data
    if msg.channel_id:
        payload["channelId"] = msg.channel_id
    return payload


def _chunk(items: list[PushMessage], size: int) -> list[list[PushMessage]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


async def send_batch(
    messages: list[PushMessage],
    timeout: float = DEFAULT_TIMEOUT,
) -> PushSendResult:
    """Expo Push API 배치 호출 — 최대 100/요청 분할 자동 처리.

    Returns:
        PushSendResult — 성공·실패 카운트, 비활성화할 토큰 목록.
    """
    if not messages:
        return PushSendResult(0, 0, 0, [], [])

    succeeded = 0
    failed = 0
    invalid_tokens: list[str] = []
    raw_responses: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for chunk in _chunk(messages, MAX_BATCH):
            payload = [_to_expo_payload(m) for m in chunk]
            try:
                resp = await client.post(
                    EXPO_PUSH_URL,
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                raw_responses.append(data)

                # Expo 응답: {"data": [{"status": "ok"|"error", "message"?, "details"?}, ...]}
                tickets = data.get("data", []) or []
                for idx, ticket in enumerate(tickets):
                    if ticket.get("status") == "ok":
                        succeeded += 1
                    else:
                        failed += 1
                        details = ticket.get("details") or {}
                        if details.get("error") == "DeviceNotRegistered":
                            invalid_tokens.append(chunk[idx].to)
            except httpx.HTTPError as e:
                # 배치 전체 실패 (네트워크 / 5xx)
                failed += len(chunk)
                log.warning("Expo push 배치 실패: %s", e)
                raw_responses.append({"error": str(e), "batch_size": len(chunk)})

    return PushSendResult(
        sent=len(messages),
        succeeded=succeeded,
        failed=failed,
        invalid_tokens=invalid_tokens,
        raw_responses=raw_responses,
    )


def is_expo_token(token: str) -> bool:
    """Expo Push Token 포맷 검증.

    Expo 토큰: ExponentPushToken[xxxx]
    FCM 토큰: 비포맷 (네이티브 raw FCM 사용 시 별도 처리)
    """
    return token.startswith("ExponentPushToken[") and token.endswith("]")

"""Solapi (CoolSMS) 카카오 알림톡 + LMS 폴백 발송.

진짜 해자 ❶: 3개월·6개월 후 follow-up.
카카오 알림톡 (사전 등록 템플릿) 우선 → 실패 시 LMS.

설계:
  - SOLAPI_API_KEY / SOLAPI_API_SECRET 환경변수 (HMAC-SHA256 인증)
  - 키 없으면 MockSolapiAdapter (test/dev)
  - 카카오 채널 ID·템플릿 코드 환경변수
  - 발송 결과 NotificationLog 에 기록 (선택)

미발송 정책:
  - PII 보호: phone 직접 노출 금지, masked 만 로그 (010-XXXX-1234)
  - 1회 실패 → LMS 폴백 → 2회 실패 → 알림 로그에 fail 기록 → cron retry X
  - 수신거부 (사용자 marketing_consent=False) → 정보성만 발송 가능
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx


class SolapiError(Exception):
    """Solapi 발송 실패."""


def mask_phone(phone: str) -> str:
    """010-1234-5678 → 010-XXXX-5678 (로그용)."""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 8:
        return "XXX-XXXX"
    return f"{digits[:3]}-XXXX-{digits[-4:]}"


def _solapi_signature(secret: str, date_str: str, salt: str) -> str:
    """Solapi HMAC-SHA256(date + salt, secret)."""
    msg = (date_str + salt).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


@dataclass(slots=True, frozen=True)
class SendResult:
    success: bool
    provider_msg_id: str | None
    channel: str        # alimtalk / lms / mock
    error: str | None
    raw: dict[str, Any]


class SolapiAdapter(Protocol):
    async def send_alimtalk(
        self,
        to: str,
        pf_id: str,
        template_id: str,
        variables: dict[str, str],
    ) -> SendResult: ...

    async def send_lms(self, to: str, text: str) -> SendResult: ...


class SolapiHttpAdapter:
    """Solapi REST 어댑터 — https://api.solapi.com/messages/v4."""

    BASE = "https://api.solapi.com"

    def __init__(self, api_key: str, api_secret: str, from_number: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.from_number = from_number

    def _auth_header(self) -> dict[str, str]:
        date_str = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        salt = secrets.token_hex(16)
        sig = _solapi_signature(self.api_secret, date_str, salt)
        return {
            "Authorization": (
                f"HMAC-SHA256 apiKey={self.api_key}, date={date_str}, "
                f"salt={salt}, signature={sig}"
            ),
            "Content-Type": "application/json",
        }

    async def send_alimtalk(
        self,
        to: str,
        pf_id: str,
        template_id: str,
        variables: dict[str, str],
    ) -> SendResult:
        payload = {
            "message": {
                "to": to,
                "from": self.from_number,
                "type": "ATA",
                "kakaoOptions": {
                    "pfId": pf_id,
                    "templateId": template_id,
                    "variables": variables,
                },
            },
        }
        return await self._post("/messages/v4/send", payload, "alimtalk")

    async def send_lms(self, to: str, text: str) -> SendResult:
        payload = {
            "message": {
                "to": to,
                "from": self.from_number,
                "type": "LMS",
                "text": text,
            },
        }
        return await self._post("/messages/v4/send", payload, "lms")

    async def _post(self, path: str, payload: dict, channel: str) -> SendResult:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.BASE}{path}",
                    headers=self._auth_header(),
                    json=payload,
                )
        except httpx.HTTPError as e:
            return SendResult(False, None, channel, str(e), {})

        if resp.status_code >= 400:
            return SendResult(
                False, None, channel,
                f"HTTP {resp.status_code}", {"text": resp.text[:200]},
            )

        try:
            data = resp.json()
        except ValueError:
            return SendResult(False, None, channel, "invalid_json", {})

        msg_id = data.get("messageId") or (data.get("message") or {}).get("messageId")
        # status 코드 2000 = 성공
        status_code = data.get("statusCode")
        success = status_code in (None, "2000")
        return SendResult(success, msg_id, channel, None if success else status_code, data)


class MockSolapiAdapter:
    """테스트/키 없는 환경 — 항상 성공."""

    async def send_alimtalk(
        self,
        to: str,
        pf_id: str,
        template_id: str,
        variables: dict[str, str],
    ) -> SendResult:
        return SendResult(True, f"mock_at_{template_id}", "alimtalk", None,
                          {"mock": True, "to_masked": mask_phone(to), "vars": variables})

    async def send_lms(self, to: str, text: str) -> SendResult:
        return SendResult(True, "mock_lms_0001", "lms", None,
                          {"mock": True, "to_masked": mask_phone(to),
                           "text_preview": text[:30]})


def get_adapter() -> SolapiAdapter:
    """환경 키 있으면 실제, 없으면 mock."""
    key = os.environ.get("SOLAPI_API_KEY")
    secret = os.environ.get("SOLAPI_API_SECRET")
    sender = os.environ.get("SOLAPI_FROM_NUMBER", "")
    if not (key and secret and sender):
        return MockSolapiAdapter()
    return SolapiHttpAdapter(key, secret, sender)


# ── 자평 도메인 메시지 빌더 ────────────────────────────
def build_followup_message(months: int, decision_label: str) -> str:
    """3개월/6개월 follow-up LMS 폴백 문구.

    자평 카피 가드 준수 — "100%·반드시·놓치면" 금지.
    """
    if months == 3:
        return (
            f"[자평] 3개월 전 '{decision_label[:20]}' 결정, 어떻게 되셨나요?\n\n"
            "지금 만족도를 한 줄로 남기시면 6개월 뒤 같은 흐름을\n"
            "더 정확히 풀어드릴 수 있습니다.\n\n"
            "▶ 응답 (30초): https://japyeong.com/f\n"
            "수신거부 080-XXX-XXXX"
        )
    return (
        f"[자평] 6개월 전 '{decision_label[:20]}' 결정 — 만족도를 마지막으로 한 번만\n"
        "남겨주시면 다음 큰 결정 때 보내드릴 자료에 반영됩니다.\n\n"
        "▶ 응답 (30초): https://japyeong.com/f\n"
        "수신거부 080-XXX-XXXX"
    )


async def send_followup(
    phone: str,
    months: int,
    decision_label: str,
    use_alimtalk: bool = True,
) -> SendResult:
    """follow-up 발송 — 알림톡 우선, 실패 시 LMS."""
    adapter = get_adapter()

    if use_alimtalk:
        pf_id = os.environ.get("KAKAO_PF_ID", "")
        template_id = os.environ.get(
            f"KAKAO_TEMPLATE_FOLLOWUP_{months}M",
            os.environ.get("KAKAO_TEMPLATE_FOLLOWUP", ""),
        )
        if pf_id and template_id:
            result = await adapter.send_alimtalk(
                to=phone,
                pf_id=pf_id,
                template_id=template_id,
                variables={
                    "#{months}": str(months),
                    "#{decision}": decision_label[:20],
                },
            )
            if result.success:
                return result
            # 알림톡 실패 → LMS 폴백

    return await adapter.send_lms(phone, build_followup_message(months, decision_label))

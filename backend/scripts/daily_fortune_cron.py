"""일진 알림 daily push cron — 매일 새벽 활성 사용자 전체 발송.

실행:
    # 모든 활성 사용자
    python -m src.scripts.daily_fortune_cron

    # 특정 시간대 (08:00 사용자만 — 사용자별 발송 시간 분산)
    python -m src.scripts.daily_fortune_cron --hour 08

    # dry run (DB 조회 + 메시지 생성만, 실 발송 X)
    python -m src.scripts.daily_fortune_cron --dry-run

권장 cron:
    # 매시간 정각 — 해당 시간대 사용자만 발송
    0 * * * *  cd /app && python -m src.scripts.daily_fortune_cron --hour $(date +\\%H)

자평 가드:
  - notif_daily_enabled = False 사용자 자동 스킵
  - notif_negative_muted = True 사용자에게 주의/흉 일진 자동 스킵
  - 위기 키워드 감지 시 1393 안내 (자평 정체성)
  - DeviceNotRegistered 토큰 자동 비활성화

환경변수:
    DATABASE_URL  — 실 DB (없으면 dry run only)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import UTC, date, datetime
from pathlib import Path

# import 경로
_THIS = Path(__file__).resolve()
_BACKEND_ROOT = _THIS.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from src.engine.daily_fortune import (  # noqa: E402
    DailyFortune,
    compute_daily_fortune,
)
from src.engine.schema import FourPillars  # noqa: E402
from src.services.birth_record_service import safe_decrypt_to_pillars  # noqa: E402
from src.services.expo_push_service import (  # noqa: E402
    PushMessage,
    PushSendResult,
    send_batch,
)

log = logging.getLogger("daily_fortune_cron")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _db_enabled() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


async def fetch_targets(hour_filter: int | None) -> list[dict]:
    """발송 대상 조회.

    Returns:
        [{user_id, push_token, platform, pillars, notif_negative_muted}, ...]

    조건:
      - user.is_active = True
      - user.notif_daily_enabled = True
      - user.notif_daily_time_hhmm 의 hour 부분이 hour_filter 와 일치 (옵션)
      - push_token.is_active = True
      - birth_record 존재 (사주 계산 가능)
    """
    if not _db_enabled():
        log.info("DATABASE_URL 미설정 — 빈 대상 리스트.")
        return []

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import selectinload

    from src.core.db import _session_factory
    from src.models.db_models import User

    session: AsyncSession
    async with _session_factory()() as session:
        stmt = (
            select(User)
            .where(User.is_active)
            .where(User.notif_daily_enabled)
            .where(User.deleted_at.is_(None))
            .options(
                selectinload(User.push_tokens),
                selectinload(User.birth_records),
            )
        )
        if hour_filter is not None:
            hh = f"{hour_filter:02d}"
            stmt = stmt.where(User.notif_daily_time_hhmm.like(f"{hh}:%"))
        users = (await session.execute(stmt)).scalars().all()

        targets: list[dict] = []
        for u in users:
            # 활성 토큰만
            active_tokens = [t for t in u.push_tokens if t.is_active]
            if not active_tokens:
                continue
            # 본인 사주 (첫 번째 BirthRecord — Sprint 5-6 이후 메인 가족 우선 로직 도입)
            if not u.birth_records:
                continue
            br = u.birth_records[0]
            # TODO Sprint 1-2: encrypted_payload 복호화 → FourPillars 변환
            # 현재는 birth_record 만 있는 상태로 처리 불가 → 패스
            pillars = _decrypt_to_pillars(br)
            if pillars is None:
                continue

            for tok in active_tokens:
                targets.append({
                    "user_id": u.id,
                    "push_token_id": tok.id,
                    "token": tok.token,
                    "platform": tok.platform,
                    "pillars": pillars,
                    "notif_negative_muted": u.notif_negative_muted,
                })

    log.info("발송 대상 %d 건 조회 (hour_filter=%s)", len(targets), hour_filter)
    return targets


def _decrypt_to_pillars(birth_record) -> FourPillars | None:
    """birth_record.encrypted_payload → FourPillars.

    PII_ENCRYPTION_KEY 환경변수 + 정상 payload 모두 충족 시 FourPillars 반환.
    하나라도 실패하면 None (cron 은 해당 사용자만 스킵, 다른 사용자에 영향 없음).
    """
    if not birth_record or not birth_record.encrypted_payload:
        return None
    return safe_decrypt_to_pillars(birth_record.encrypted_payload)


def build_message(target: dict, fortune: DailyFortune) -> PushMessage | None:
    """대상자 prefs 반영해 PushMessage 생성. 스킵 시 None."""
    # 부정 통변 끄기 — 주의/흉 자동 스킵 (자평 가드 #9)
    if target.get("notif_negative_muted") and fortune.label in ("주의", "흉"):
        return None

    data = {
        "type": "daily_fortune",
        "date": fortune.date.isoformat(),
        "label": fortune.label,
        "score": fortune.score,
        "day_pillar": f"{fortune.day_pillar.gan}{fortune.day_pillar.ji}",
        "areas": fortune.suggested_areas,
    }

    return PushMessage(
        to=target["token"],
        title=fortune.title,
        body=fortune.body,
        data=data,
        channel_id="daily-fortune",
    )


async def deactivate_invalid_tokens(invalid_tokens: list[str]) -> None:
    """DeviceNotRegistered 받은 토큰 자동 비활성화."""
    if not invalid_tokens or not _db_enabled():
        return

    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import PushToken

    session: AsyncSession
    async with _session_factory()() as session:
        stmt = (
            update(PushToken)
            .where(PushToken.token.in_(invalid_tokens))
            .values(is_active=False, last_error="DeviceNotRegistered")
        )
        await session.execute(stmt)
        await session.commit()
        log.info("DeviceNotRegistered 토큰 %d개 비활성화", len(invalid_tokens))


async def log_notifications(
    targets: list[dict],
    messages: list[PushMessage],
    result: PushSendResult,
) -> None:
    """발송 결과 notification_log 저장 (감사용)."""
    if not _db_enabled() or not messages:
        return

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.core.db import _session_factory
    from src.models.db_models import NotificationLog

    # message → target 매핑 (token 기준)
    token_to_target = {t["token"]: t for t in targets}
    invalid_set = set(result.invalid_tokens)

    session: AsyncSession
    async with _session_factory()() as session:
        for m in messages:
            tgt = token_to_target.get(m.to)
            if not tgt:
                continue
            status = "error" if m.to in invalid_set else "ok"
            session.add(NotificationLog(
                user_id=tgt["user_id"],
                push_token_id=tgt["push_token_id"],
                notification_type="daily_fortune",
                title=m.title,
                body=m.body,
                status=status,
                provider_response={"sent_at": datetime.now(UTC).isoformat()},
            ))
        await session.commit()


async def main() -> int:
    parser = argparse.ArgumentParser(description="자평 일진 daily push cron")
    parser.add_argument(
        "--hour", type=int, default=None,
        help="발송 대상 hour 필터 (예: 8 → 08:* 사용자만)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실 발송 안 함, 메시지 생성·로그만",
    )
    args = parser.parse_args()

    today = date.today()
    log.info("=== 일진 알림 cron 시작 · %s · hour=%s · dry=%s ===",
             today.isoformat(), args.hour, args.dry_run)

    targets = await fetch_targets(args.hour)
    if not targets:
        log.info("발송 대상 0건 — 종료.")
        return 0

    # 각 대상자별 메시지 생성
    messages: list[PushMessage] = []
    skipped_negative = 0
    for tgt in targets:
        fortune = compute_daily_fortune(tgt["pillars"], today)
        m = build_message(tgt, fortune)
        if m is None:
            skipped_negative += 1
            continue
        messages.append(m)

    log.info("메시지 생성: %d 건 (negative_muted 스킵: %d)",
             len(messages), skipped_negative)

    if args.dry_run:
        log.info("--dry-run — 발송 생략. 첫 3건 미리보기:")
        for m in messages[:3]:
            log.info("  %s: %s | %s", m.to[:30], m.title, m.body[:60])
        return 0

    # Expo Push 배치 발송
    result = await send_batch(messages)
    log.info(
        "발송 결과: sent=%d succeeded=%d failed=%d invalid=%d",
        result.sent, result.succeeded, result.failed, len(result.invalid_tokens),
    )

    # 비활성 토큰 처리 + 로그 저장
    await deactivate_invalid_tokens(result.invalid_tokens)
    await log_notifications(targets, messages, result)

    # 요약 출력 (운영 모니터링)
    summary = {
        "date": today.isoformat(),
        "hour_filter": args.hour,
        "targets": len(targets),
        "messages_built": len(messages),
        "skipped_negative_muted": skipped_negative,
        "sent": result.sent,
        "succeeded": result.succeeded,
        "failed": result.failed,
        "invalidated_tokens": len(result.invalid_tokens),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

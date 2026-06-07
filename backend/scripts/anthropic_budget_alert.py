"""Anthropic Budget Alert — LLM 비용 폭주 자동 셧다운.

자평 정체성 보험 ❸ 보강 — Rate limit 다층 방어와 짝.

실행 방법:
    # 매시간 cron 또는 Vercel cron (vercel.json crons)
    python -m src.scripts.anthropic_budget_alert

    # 환경변수
    ANTHROPIC_ADMIN_API_KEY = sk-ant-admin-...  (Anthropic Admin API 키, Org owner 필요)
    SLACK_WEBHOOK_URL       = https://hooks.slack.com/...  (선택)
    BUDGET_DAILY_KRW        = 3000000  (300만 = 자동 셧다운 임계, 기본)
    BUDGET_HOURLY_ALERT_KRW = 500000   (50만 = 시간당 알림 임계)
    USD_TO_KRW              = 1370     (환율, 일간 갱신 권장)

임계 (BM v2 검증 반영):
    - 일 50만원: Slack 알림 ("모니터링 강화")
    - 일 100만원: Slack + 대표 SMS ("무료 티어 일시 차단 검토")
    - 일 300만원: 자동 셧다운 ("무료 티어 차단, 유료만 유지")

산출:
    - stdout: 사용량 요약 JSON
    - 환경변수 ANTHROPIC_KILL_SWITCH_PATH 가 있고 임계 초과 시 그 파일에
      kill switch 마커 작성 → API 핸들러가 그 파일 존재 여부로 무료 티어 차단
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from urllib import error, request

# ── 임계 (BM v2 — 환경변수로 override 가능) ──────────────────
BUDGET_DAILY_KRW_HARD = int(os.environ.get("BUDGET_DAILY_KRW", "3000000"))
BUDGET_HOURLY_ALERT_KRW = int(os.environ.get("BUDGET_HOURLY_ALERT_KRW", "500000"))
USD_TO_KRW = float(os.environ.get("USD_TO_KRW", "1370"))

ANTHROPIC_ADMIN_KEY = os.environ.get("ANTHROPIC_ADMIN_API_KEY", "")
ANTHROPIC_ORG_ID = os.environ.get("ANTHROPIC_ORG_ID", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
KILL_SWITCH_PATH = os.environ.get(
    "ANTHROPIC_KILL_SWITCH_PATH", "/tmp/japyeong-anthropic-kill-switch",
)


@dataclass
class UsageReport:
    today_usd: float
    today_krw: int
    yesterday_usd: float
    month_to_date_usd: float
    threshold_breached: str | None  # "alert" | "hard" | None


def fetch_anthropic_usage() -> UsageReport:
    """Anthropic Admin API 의 Usage 엔드포인트 호출.

    문서: https://docs.anthropic.com/en/api/admin-api/usage

    Admin API 키가 없으면 더미 0 값 반환 (CI / 로컬 테스트용).
    """
    if not ANTHROPIC_ADMIN_KEY or not ANTHROPIC_ORG_ID:
        print("⚠ ANTHROPIC_ADMIN_API_KEY / ANTHROPIC_ORG_ID 미설정 — 더미 보고")
        return UsageReport(0.0, 0, 0.0, 0.0, None)

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    month_start = date.today().replace(day=1).isoformat()

    base = "https://api.anthropic.com/v1/organizations/{org}/usage_report/messages"
    url = base.format(org=ANTHROPIC_ORG_ID)

    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
    }

    def _fetch(starting_at: str, ending_at: str | None = None) -> float:
        params = f"?starting_at={starting_at}T00:00:00Z"
        if ending_at:
            params += f"&ending_at={ending_at}T00:00:00Z"
        req = request.Request(url + params, headers=headers)
        try:
            with request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                total = 0.0
                for r in data.get("data", []):
                    for result in r.get("results", []):
                        total += float(result.get("cost", {}).get("amount", 0))
                return total
        except (error.HTTPError, error.URLError, json.JSONDecodeError) as e:
            print(f"⚠ Anthropic Usage API 오류: {e}")
            return 0.0

    today_usd = _fetch(today)
    yesterday_usd = _fetch(yesterday, today)
    mtd_usd = _fetch(month_start)

    today_krw = int(today_usd * USD_TO_KRW)

    breached: str | None = None
    if today_krw >= BUDGET_DAILY_KRW_HARD:
        breached = "hard"
    elif today_krw >= BUDGET_HOURLY_ALERT_KRW:
        breached = "alert"

    return UsageReport(
        today_usd=today_usd,
        today_krw=today_krw,
        yesterday_usd=yesterday_usd,
        month_to_date_usd=mtd_usd,
        threshold_breached=breached,
    )


def post_slack(message: str) -> None:
    """Slack 알림 발송 (옵션)."""
    if not SLACK_WEBHOOK_URL:
        return
    try:
        payload = json.dumps({"text": message}).encode("utf-8")
        req = request.Request(
            SLACK_WEBHOOK_URL, data=payload,
            headers={"Content-Type": "application/json"},
        )
        request.urlopen(req, timeout=5)
    except (error.HTTPError, error.URLError) as e:
        print(f"⚠ Slack 알림 실패: {e}")


def activate_kill_switch(reason: str) -> None:
    """무료 티어 자동 셧다운 마커 파일 생성.

    API 핸들러는 시작 시 이 파일 존재 여부를 확인해 무료 티어 요청을 차단.
    """
    try:
        ts = datetime.now(UTC).isoformat()
        with open(KILL_SWITCH_PATH, "w") as f:
            f.write(f"{ts}\n{reason}\n")
        print(f"🔒 KILL SWITCH ACTIVATED: {KILL_SWITCH_PATH}")
        print(f"   사유: {reason}")
    except OSError as e:
        print(f"⚠ Kill switch 파일 작성 실패: {e}")


def main() -> int:
    """매시간 실행 — 사용량 조회 → 임계 비교 → 알림·셧다운."""
    report = fetch_anthropic_usage()
    summary = {
        "checked_at": datetime.now(UTC).isoformat(),
        "today_usd": round(report.today_usd, 2),
        "today_krw": report.today_krw,
        "yesterday_usd": round(report.yesterday_usd, 2),
        "month_to_date_usd": round(report.month_to_date_usd, 2),
        "threshold_breached": report.threshold_breached,
        "budget_daily_krw_hard": BUDGET_DAILY_KRW_HARD,
        "budget_hourly_alert_krw": BUDGET_HOURLY_ALERT_KRW,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if report.threshold_breached == "alert":
        msg = (
            f"⚠ 자평 LLM 비용 알림 — 오늘 {report.today_krw:,}원 사용 "
            f"(임계 {BUDGET_HOURLY_ALERT_KRW:,}원 초과). "
            "모니터링 강화 필요."
        )
        print(msg)
        post_slack(msg)
        return 0

    if report.threshold_breached == "hard":
        msg = (
            f"🔥 자평 LLM 비용 HARD 임계 — 오늘 {report.today_krw:,}원 사용 "
            f"(임계 {BUDGET_DAILY_KRW_HARD:,}원 초과). "
            "무료 티어 자동 셧다운 발동."
        )
        print(msg)
        post_slack(msg)
        activate_kill_switch(msg)
        return 1  # exit code 1 = 셧다운 발동

    return 0


if __name__ == "__main__":
    sys.exit(main())

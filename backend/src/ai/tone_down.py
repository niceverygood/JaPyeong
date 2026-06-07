"""단정 표현 자동 톤다운 — 자평 정체성 보험 ❷.

CLAUDE 응답에서 단정형 한국어 어휘를 자동으로 절제 표현으로 변환.
LLM이 가끔 (학파 견해 갈리는 영역에서) 단정형으로 답할 때를 대비한 후처리 안전망.

원칙:
  - 미래 단정 ("할 것이다") → 가능성 ("할 가능성이 있다")
  - 절대 표현 ("100%", "반드시") → 약화 ("높은 확률", "주로")
  - 부작위 손해 ("놓치면 손해") → 권유 ("지금 보면 좋습니다")
  - 결과 보장 ("운이 좋아진다") → 약화 ("좋은 흐름으로 볼 수 있습니다")

순수 정규식. 결정론적. 빈 입력은 빈 출력.
한자 자동 병기(annotate_hanja) 뒤에 적용하는 게 좋음 — 글자 변환과 충돌 없음.

⚠ 제거 우선순위:
  HIGH (반드시) - 표시광고법 부당 표시 위험
  MED          - 자평 정체성 ("절제된 어법")
  LOW          - 스타일링
"""

from __future__ import annotations

import re

# ── 규칙 (순서 중요 — 위에서부터 적용) ─────────────────────
# (정규식, 대체 문자열, 우선순위 라벨)
_RULES: list[tuple[re.Pattern[str], str, str]] = [
    # ── HIGH: 절대 표현 (표시광고법 부당 표시 위험) ────────
    (re.compile(r"100\s*%\s*적중"), "명리 고전 해석 기반", "HIGH"),
    (re.compile(r"100\s*%\s*정확"), "명리 고전 해석 기반", "HIGH"),
    (re.compile(r"적중률\s*[0-9]+%"), "명리 고전 해석", "HIGH"),
    (re.compile(r"100\s*%"), "높은 확률로", "HIGH"),  # 단독 "100%" 잔여 처리
    (re.compile(r"반드시\s+(\w+)"), r"\1 가능성이 큽니다", "HIGH"),
    (re.compile(r"분명히\s+(\w+)"), r"\1 가능성이 있습니다", "HIGH"),
    (re.compile(r"확실히\s+(\w+)"), r"\1 흐름이 보입니다", "HIGH"),
    (re.compile(r"틀림없이\s+(\w+)"), r"\1 흐름이 보입니다", "HIGH"),
    (re.compile(r"정확히\s+(\w+)"), r"\1 흐름이 보입니다", "HIGH"),

    # ── HIGH: 부작위 손해 단정 ─────────────────────────────
    (re.compile(r"놓치면\s+손해"), "지금 보면 좋습니다", "HIGH"),
    (re.compile(r"안\s*보면\s+(손해|위험|불이익)"), "지금 보면 도움이 됩니다", "HIGH"),
    (re.compile(r"모르면\s+(손해|위험|불이익)"), "알아두시면 도움이 됩니다", "HIGH"),
    (re.compile(r"위기\s*시기\s*알림"), "주의 깊게 볼 구간 표시", "HIGH"),

    # ── HIGH: 결과 보장 ─────────────────────────────────────
    (re.compile(r"운이\s+좋아진다"), "좋은 흐름으로 볼 수 있습니다", "HIGH"),
    (re.compile(r"운이\s+나빠진다"), "주의 깊게 볼 흐름이 있습니다", "HIGH"),
    (re.compile(r"운명\s*을?\s*바꾼다"), "흐름을 다듬을 수 있습니다", "HIGH"),
    (re.compile(r"운명\s*을?\s*바꿔"), "흐름을 다듬어", "HIGH"),
    (re.compile(r"운명\s*을?\s*바꾸(?=\w)"), "흐름을 다듬", "HIGH"),  # "바꾸고/바꾸면" 등 어간
    (re.compile(r"성공한다"), "성공할 가능성이 있습니다", "HIGH"),
    (re.compile(r"실패한다"), "주의가 필요할 수 있습니다", "HIGH"),

    # ── MED: 미래 단정형 (자평 정체성) ─────────────────────
    # "~할 것이다" / "~할 것입니다" → "~할 가능성이 있습니다"
    (re.compile(r"(\w+)할\s*것이다"), r"\1할 가능성이 있다", "MED"),
    (re.compile(r"(\w+)할\s*것입니다"), r"\1할 가능성이 있습니다", "MED"),
    (re.compile(r"(\w+)할\s*것이며"), r"\1할 가능성이 있으며", "MED"),
    (re.compile(r"(\w+)할\s*것입니다만"), r"\1할 가능성이 있습니다만", "MED"),
    # "~된다" 단정 → "~될 수 있다" (광범위, LOW 우선순위)
    (re.compile(r"(됩니|됩|된)다(?!고)"), r"\1다 가능성이 있다", "LOW"),

    # ── MED: 의학·법률·재무 단정 ───────────────────────────
    (
        re.compile(r"이\s*(병|증세)\s*(이|가)?\s*(나아진다|낫는다|치료된다)"),
        "건강 흐름을 주의 깊게 살피시기 권합니다",
        "HIGH",
    ),
    (
        re.compile(r"이\s*(주식|투자)\s*(이|가)?\s*(오른다|상승한다)"),
        "재정 흐름은 전문가와 상의를 권합니다",
        "HIGH",
    ),
    (
        re.compile(r"이\s*(주식|투자)\s*(이|가)?\s*(내린다|하락한다)"),
        "재정 흐름은 전문가와 상의를 권합니다",
        "HIGH",
    ),
]

# 단순한 LOW 규칙 (위 _RULES에 포함 안 한 것)
_LOW_RULES = (
    (re.compile(r"이\s*된다(?!고)"), "일 가능성이 있다"),
)


def tone_down(text: str, strict: bool = True) -> str:
    """단정 표현을 절제 표현으로 변환.

    Args:
        text: 변환할 텍스트 (빈 문자열·None 입력 시 그대로 반환).
        strict: True 면 HIGH+MED 적용, False 면 HIGH 만 적용 (보수적).

    Returns:
        변환된 텍스트.
    """
    if not text:
        return text

    out = text
    for pattern, replacement, severity in _RULES:
        if severity == "LOW":
            continue  # LOW 는 옵션 비활성화 (오탐 가능)
        if not strict and severity == "MED":
            continue
        out = pattern.sub(replacement, out)

    return out


def detect_forbidden(text: str) -> list[str]:
    """텍스트에서 금지 어휘를 찾아 리스트 반환 (감사·로깅용).

    톤다운으로 잡히지 않은 잔여 위험 표현 모니터링.
    """
    if not text:
        return []
    findings: list[str] = []
    monitors = (
        r"100\s*%",
        r"반드시",
        r"분명히",
        r"확실히",
        r"적중률",
        r"놓치면\s*손해",
        r"위기\s*시기",
        r"운명\s*을?\s*바꾼다",
    )
    for pat in monitors:
        m = re.search(pat, text)
        if m:
            findings.append(m.group(0))
    return findings

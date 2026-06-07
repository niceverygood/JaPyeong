"""ai.tone_down 단위 테스트.

자평 정체성 보험 ❷ — 단정 표현 자동 톤다운.
표시광고법 부당 표시 위험 어휘가 LLM 응답에 섞일 때 후처리로 자동 약화.
"""

from __future__ import annotations

import pytest

from src.ai.tone_down import detect_forbidden, tone_down


# ── 빈 입력 ────────────────────────────────────────────────
def test_empty_input() -> None:
    assert tone_down("") == ""
    assert tone_down(None) is None  # type: ignore[arg-type]


def test_no_forbidden_unchanged() -> None:
    src = "이 사주에서 식신생재격으로 볼 수 있는 흐름이 있습니다."
    assert tone_down(src) == src


# ── HIGH 우선순위: 표시광고법 위험 ──────────────────────
def test_100_percent_removed() -> None:
    assert "100%" not in tone_down("100% 적중한다")
    assert "명리 고전 해석 기반" in tone_down("100% 적중하는 사주")


def test_절대표현_반드시() -> None:
    out = tone_down("반드시 성공한다")
    # "반드시 X" → "X 가능성이 큽니다" + "성공한다" → "성공할 가능성이 있습니다"
    # 둘 다 적용되어도 "반드시" 가 사라져야 함
    assert "반드시" not in out


def test_절대표현_분명히() -> None:
    assert "분명히" not in tone_down("분명히 결혼한다")


def test_절대표현_확실히() -> None:
    assert "확실히" not in tone_down("확실히 잘된다")


def test_적중률_X퍼센트() -> None:
    out = tone_down("적중률 99% 보장")
    assert "99%" not in out
    assert "적중률" not in out


# ── HIGH: 부작위 손해 ─────────────────────────────────────
def test_놓치면_손해() -> None:
    out = tone_down("이번 기회를 놓치면 손해입니다")
    assert "놓치면 손해" not in out
    assert "지금 보면 좋습니다" in out


def test_위기_시기_알림() -> None:
    out = tone_down("위기 시기 알림 서비스")
    assert "위기 시기" not in out


def test_안보면_위험() -> None:
    out = tone_down("지금 안 보면 위험합니다")
    assert "위험" not in out or "안 보면" not in out


# ── HIGH: 결과 보장 ───────────────────────────────────────
def test_운이_좋아진다() -> None:
    out = tone_down("이걸 사면 운이 좋아진다")
    assert "운이 좋아진다" not in out
    assert "좋은 흐름으로" in out


def test_운명_바꾼다() -> None:
    out = tone_down("자평이 당신의 운명을 바꿉니다")
    # "운명을 바꾼다" 또는 "운명을 바꾸" 패턴 변환
    assert "운명을 바꾼" not in out and "운명 바꾼" not in out


def test_성공한다() -> None:
    out = tone_down("이번에 성공한다")
    assert "성공한다" not in out
    assert "가능성이 있" in out


# ── HIGH: 의학·법률·재무 ──────────────────────────────────
def test_의학_단정() -> None:
    out = tone_down("이 병이 나아진다")
    assert "나아진다" not in out
    assert "건강 흐름" in out


def test_재무_단정() -> None:
    out = tone_down("이 주식이 오른다")
    assert "오른다" not in out
    assert "전문가와 상의" in out


# ── MED: 미래 단정형 (strict=True 일 때만 적용) ─────────
def test_미래단정_할것이다_strict() -> None:
    out = tone_down("이직할 것이다", strict=True)
    assert "할 것이다" not in out
    assert "가능성이 있" in out


def test_미래단정_strict_off() -> None:
    # strict=False 면 MED 규칙 안 적용 → 미래 단정 유지
    out = tone_down("이직할 것이다", strict=False)
    assert "할 것이다" in out


def test_할것입니다() -> None:
    out = tone_down("결혼할 것입니다")
    assert "할 것입니다" not in out
    assert "가능성이 있" in out


# ── detect_forbidden — 감사·모니터링 ───────────────────────
def test_detect_clean() -> None:
    assert detect_forbidden("정관격으로 볼 수 있는 흐름") == []


def test_detect_forbidden_words() -> None:
    findings = detect_forbidden("반드시 100% 적중률 분명히")
    assert len(findings) >= 3  # 반드시, 100%, 적중률, 분명히
    assert any("100" in f for f in findings)
    assert any("반드시" in f for f in findings)


def test_detect_empty() -> None:
    assert detect_forbidden("") == []
    assert detect_forbidden(None) == []  # type: ignore[arg-type]


# ── 결합 테스트: 실제 LLM 응답 시나리오 ─────────────────────
@pytest.mark.parametrize("src,forbidden", [
    ("당신은 반드시 결혼할 것입니다.", ["반드시"]),
    ("이 사주는 100% 부자가 되는 사주입니다.", ["100%"]),
    ("놓치면 손해니까 지금 바로 결정하세요.", ["놓치면 손해"]),
    ("운명을 바꾸고 싶다면 자평을 이용하세요.", ["운명을 바꾸"]),
])
def test_realistic_llm_responses(src: str, forbidden: list[str]) -> None:
    """실제 LLM이 잘못 답할 수 있는 시나리오."""
    out = tone_down(src)
    for word in forbidden:
        assert word not in out, f"'{word}' 가 톤다운 후에도 남아있음: {out}"

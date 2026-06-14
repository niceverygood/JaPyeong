"""골든 검증셋 정확도 — 신강약/용신 정답률 측정 + 회귀 방어.

data/validation_cases/golden_*.json 의 명조를 엔진에 넣어 기대 라벨과 비교한다.
'논쟁 없는' 케이스만 골든셋에 두므로, 정답률이 일정 바를 넘어야 통과한다.
정확도가 곧 신뢰 — 이 테스트가 깨지면 엔진 정확도 회귀를 의미한다.
"""

from __future__ import annotations

import glob
import json
import os

import pytest

from src.engine import strength as st
from src.engine import yongsin as ys
from src.engine.constants import Ohaeng
from src.engine.schema import FourPillars, Pillar

_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "validation_cases", "golden"
)

# 신강약 정답률 하한(골든은 명백한 케이스라 높게).
STRENGTH_ACCURACY_BAR = 0.85
# 용신은 유파 차가 커 라벨 있는 케이스만, 다소 낮은 바.
YONGSIN_ACCURACY_BAR = 0.60


def _load_cases() -> list[dict]:
    cases: list[dict] = []
    for path in sorted(glob.glob(os.path.join(_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for c in data.get("cases", []):
            c["_file"] = os.path.basename(path)
            cases.append(c)
    return cases


def _pillars(c: dict) -> FourPillars:
    def P(gz: str | None) -> Pillar | None:
        if not gz or len(gz) < 2:
            return None
        return Pillar(gan=gz[0], ji=gz[1])

    hour = P(c.get("hour"))
    return FourPillars(
        year=P(c["year"]), month=P(c["month"]), day=P(c["day"]),
        hour=hour if hour is not None else P(c["day"]),  # 시주 없으면 일주로 대체(분포 영향 최소)
    )


_CASES = _load_cases()


def test_golden_set_present() -> None:
    assert len(_CASES) >= 5, "골든 케이스가 너무 적습니다(시드 확인)."


@pytest.mark.skipif(not _CASES, reason="no golden cases")
def test_strength_accuracy() -> None:
    labeled = [c for c in _CASES if c.get("expect_strength")]
    assert labeled, "expect_strength 라벨 케이스가 없습니다."
    miss: list[str] = []
    for c in labeled:
        got = st.assess_strength(_pillars(c)).label
        if got != c["expect_strength"]:
            miss.append(f"[{c['_file']}:{c['id']}] 기대 {c['expect_strength']} → {got}")
    acc = 1 - len(miss) / len(labeled)
    print(f"\n신강약 정확도: {acc:.1%} ({len(labeled)-len(miss)}/{len(labeled)})")
    for m in miss:
        print("  MISS", m)
    assert acc >= STRENGTH_ACCURACY_BAR, f"신강약 정확도 {acc:.1%} < {STRENGTH_ACCURACY_BAR:.0%}\n" + "\n".join(miss)


_OHAENG_BY_CHAR = {o.value: o for o in Ohaeng}


@pytest.mark.skipif(not _CASES, reason="no golden cases")
def test_yongsin_accuracy() -> None:
    labeled = [c for c in _CASES if c.get("expect_yongsin")]
    if not labeled:
        pytest.skip("expect_yongsin 라벨 케이스 없음")
    miss: list[str] = []
    for c in labeled:
        want = _OHAENG_BY_CHAR.get(c["expect_yongsin"].strip())
        got = ys.derive_yongsin(_pillars(c)).yongsin
        if want is not None and got != want:
            miss.append(f"[{c['_file']}:{c['id']}] 기대 {c['expect_yongsin']} → {got.value}")
    acc = 1 - len(miss) / len(labeled)
    print(f"\n용신 정확도: {acc:.1%} ({len(labeled)-len(miss)}/{len(labeled)})")
    for m in miss:
        print("  MISS", m)
    assert acc >= YONGSIN_ACCURACY_BAR, f"용신 정확도 {acc:.1%} < {YONGSIN_ACCURACY_BAR:.0%}\n" + "\n".join(miss)

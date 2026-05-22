"""검증 하네스 메타 테스트.

- validation_cases/ 의 모든 JSON이 스키마를 만족하는지 검증.
- 출시 게이트: 검증 케이스 100건 이상 (RUN_GATE_CHECK=1 일 때 강제).
"""

import os

import pytest

from tests.engine._loader import case_files, load_case

CASE_FILES = case_files()


@pytest.mark.skipif(not CASE_FILES, reason="아직 검증 케이스 없음 (Phase 1 수집 예정)")
@pytest.mark.parametrize("path", CASE_FILES, ids=lambda p: p.stem)
def test_validation_case_parses(path):
    """각 검증 케이스 JSON이 ValidationCase 스키마를 만족해야 한다."""
    case = load_case(path)
    assert case.id, f"{path.name}: id 누락"
    assert case.source, f"{path.name}: source(출처) 누락 — 트레이스 불가"
    # 8자 추출 검증 케이스라면 최소 년/월/일주는 있어야 한다.
    if case.expected.pillars is not None:
        p = case.expected.pillars
        assert p.year and p.month and p.day


def test_case_ids_unique():
    """검증 케이스 id 중복 금지."""
    ids = [load_case(p).id for p in CASE_FILES]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"중복 id: {dupes}"


@pytest.mark.skipif(
    os.environ.get("RUN_GATE_CHECK") != "1",
    reason="출시 게이트 체크 (RUN_GATE_CHECK=1 로 활성화)",
)
def test_release_gate_min_100_cases():
    """정식 출시 게이트: 검증 케이스 100건 미만이면 실패."""
    assert len(CASE_FILES) >= 100, (
        f"검증 케이스 {len(CASE_FILES)}건 — 출시 기준(100건) 미달"
    )

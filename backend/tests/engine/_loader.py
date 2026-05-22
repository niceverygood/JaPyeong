"""검증 케이스 로더.

backend/data/validation_cases/*.json 을 읽어 ValidationCase 로 파싱한다.
밑줄(_)로 시작하는 파일은 템플릿/주석용으로 간주하고 건너뛴다.
"""

import json
from pathlib import Path

from src.engine.schema import ValidationCase

VALIDATION_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "validation_cases"
)


def case_files() -> list[Path]:
    if not VALIDATION_DIR.exists():
        return []
    return sorted(
        p for p in VALIDATION_DIR.glob("*.json") if not p.name.startswith("_")
    )


def load_case(path: Path) -> ValidationCase:
    data = json.loads(path.read_text(encoding="utf-8"))
    return ValidationCase.model_validate(data)


def load_all_cases() -> list[ValidationCase]:
    return [load_case(p) for p in case_files()]

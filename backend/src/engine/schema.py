"""검증 케이스 및 엔진 입출력 Pydantic 스키마.

Phase 1: 검증 케이스(ValidationCase) 스키마부터 확정한다.
엔진 각 모듈의 출력 스키마는 모듈 구현 시 점진적으로 이 파일에 통합한다.

검증 우선 개발(TDD): 모든 명리 엔진 결과는 이 스키마로 직렬화되어
검증 케이스의 expected와 대조 가능해야 한다(트레이스 가능성).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.engine.constants import GAN_SET, JI_SET

Gender = Literal["M", "F"]
Calendar = Literal["solar", "lunar"]
StrengthLabel = Literal["신강", "신약", "중화"]
DaewoonDirection = Literal["forward", "backward"]


class BirthInfo(BaseModel):
    """출생 정보 (엔진 입력)."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    gender: Gender
    calendar: Calendar = "solar"
    year: int = Field(ge=1, le=2200)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    # 음력 윤달 여부 (calendar == "lunar"일 때만 의미)
    is_leap_month: bool = False
    birth_place: str | None = None
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    timezone: str = "Asia/Seoul"


class Pillar(BaseModel):
    """기둥 하나 (천간 + 지지)."""

    model_config = ConfigDict(extra="forbid")

    gan: str
    ji: str

    @field_validator("gan")
    @classmethod
    def _check_gan(cls, v: str) -> str:
        if v not in GAN_SET:
            raise ValueError(f"유효하지 않은 천간: {v!r}")
        return v

    @field_validator("ji")
    @classmethod
    def _check_ji(cls, v: str) -> str:
        if v not in JI_SET:
            raise ValueError(f"유효하지 않은 지지: {v!r}")
        return v

    @property
    def ganji(self) -> str:
        return self.gan + self.ji


class FourPillars(BaseModel):
    """사주 4기둥(년월일시). 시주는 출생시 미상 시 생략 가능."""

    model_config = ConfigDict(extra="forbid")

    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar | None = None


class TenGodsCount(BaseModel):
    """십성(十星) 개수 분포."""

    model_config = ConfigDict(extra="forbid")

    bi_gyeon: int = 0  # 비견
    gyeop_jae: int = 0  # 겁재
    sik_sin: int = 0  # 식신
    sang_gwan: int = 0  # 상관
    jeong_jae: int = 0  # 정재
    pyeon_jae: int = 0  # 편재
    jeong_gwan: int = 0  # 정관
    pyeon_gwan: int = 0  # 편관
    jeong_in: int = 0  # 정인
    pyeon_in: int = 0  # 편인


class ExpectedResult(BaseModel):
    """검증 케이스의 기대 결과.

    모든 필드 선택적 — 케이스마다 검증하려는 항목만 채운다.
    (예: 8자 추출만 검증하는 케이스 / 격국·용신까지 검증하는 케이스)
    """

    model_config = ConfigDict(extra="forbid")

    pillars: FourPillars | None = None
    day_master: str | None = None
    day_master_strength: StrengthLabel | None = None
    geokguk: str | None = None
    yongsin: str | None = None  # 용신 (오행 또는 한자)
    huishin: str | None = None  # 희신
    gisin: str | None = None  # 기신
    gushin: str | None = None  # 구신
    daewoon_start_age: int | None = Field(default=None, ge=0, le=120)
    daewoon_direction: DaewoonDirection | None = None
    ten_gods_count: TenGodsCount | None = None

    @field_validator("day_master")
    @classmethod
    def _check_day_master(cls, v: str | None) -> str | None:
        if v is not None and v not in GAN_SET:
            raise ValueError(f"day_master는 천간이어야 함: {v!r}")
        return v


class ValidationCase(BaseModel):
    """명리 엔진 회귀 테스트 검증 케이스 1건.

    backend/data/validation_cases/*.json 의 스키마.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    source: str  # 출처 (고전·명리서·자문위원 검증 등 트레이스용)
    birth: BirthInfo
    expected: ExpectedResult
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None

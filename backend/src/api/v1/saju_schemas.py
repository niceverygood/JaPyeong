"""/v1/saju API 응답 DTO (엔진 dataclass → 직렬화용 Pydantic)."""

from datetime import date

from pydantic import BaseModel

from src.engine.schema import FourPillars, Pillar, TenGodsCount


class FiveElementsResponse(BaseModel):
    mok: float
    hwa: float
    to: float
    geum: float
    su: float
    total: float
    dominant: str  # 최강 오행 (한자)
    weakest: str  # 최약 오행 (한자)
    balance: float  # 0~1


class RelationResponse(BaseModel):
    type: str  # 관계명 (한글)
    members: list[str]  # 한자 글자
    positions: list[str]  # year_gan / month_ji ...


class DaewoonPeriodResponse(BaseModel):
    sequence: int
    start_age: int
    gan: str
    ji: str


class DaewoonResponse(BaseModel):
    direction: str  # forward | backward
    start_age: int
    periods: list[DaewoonPeriodResponse]


class NatalResponse(BaseModel):
    """원국 분석 결과."""

    pillars: FourPillars
    day_master: str
    day_master_element: str  # 일간 오행 (한자)
    ten_gods: TenGodsCount
    five_elements: FiveElementsResponse
    relations: list[RelationResponse]
    daewoon: DaewoonResponse


class LuckResponse(BaseModel):
    """특정 일자의 흐르는 운 (세운·월운·일운)."""

    date: date
    se_un: Pillar
    wol_un: Pillar
    il_un: Pillar

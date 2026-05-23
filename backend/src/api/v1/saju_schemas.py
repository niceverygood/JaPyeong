"""/v1/saju API 응답 DTO (엔진 dataclass → 직렬화용 Pydantic).

⚠ strength/geokguk/yongsin은 자문위원 미확정 상태(provisional).
각 응답 객체에 confidence 필드를 노출해 클라이언트가 명확히 표기할 수 있게 한다.
"""

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


class StrengthResponse(BaseModel):
    label: str  # 신강 / 신약 / 중화
    ally_ratio: float
    deuk_ryeong: bool
    deuk_ji: bool
    notes: list[str]
    confidence: str  # "provisional"


class GeokgukResponse(BaseModel):
    name: str  # 정관격 / 편관격 / ...
    ten_god: str  # 한글 이름 (비견·정관 등)
    based_on: str  # transparent / primary
    based_gan: str  # 격을 만든 천간
    confidence: str


class YongsinResponse(BaseModel):
    yongsin: str  # 오행 (木火土金水)
    huishin: str
    gisin: str
    gushin: str
    method: str  # eokbu / johu / hybrid
    based_on_strength: str
    notes: list[str]
    confidence: str


class NatalResponse(BaseModel):
    """원국 분석 결과."""

    pillars: FourPillars
    day_master: str
    day_master_element: str  # 일간 오행 (한자)
    ten_gods: TenGodsCount
    five_elements: FiveElementsResponse
    relations: list[RelationResponse]
    daewoon: DaewoonResponse
    strength: StrengthResponse
    geokguk: GeokgukResponse
    yongsin: YongsinResponse


class LuckResponse(BaseModel):
    """특정 일자의 흐르는 운 (세운·월운·일운)."""

    date: date
    se_un: Pillar
    wol_un: Pillar
    il_un: Pillar

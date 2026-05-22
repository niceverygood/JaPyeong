"""지장간(地藏干) — 지지 속에 감춰진 천간.

근거: 월률분야(月律分野) 지장간 통설. 명리 유파 공통이며 정책 의존이 없다.
일수 배분은 다수 교재(박재완 『명리요강』 등)에서 통용되는 30일 기준표를 채택한다.

각 지지는 餘氣(여기)·中氣(중기)·正氣(정기) 순으로 천간을 품는다.
단, 子·卯·酉(사왕지 중 일부)는 中氣 없이 餘氣·正氣 2원소만 가진다.
正氣(본기)는 그 지지의 대표 오행을 결정한다.

순수 결정론적 룩업. 같은 입력 → 항상 같은 출력.
"""

from dataclasses import dataclass
from enum import StrEnum

from src.engine.constants import JI_SET


class StageType(StrEnum):
    """지장간 단계. 값은 한자 원문(사용자 노출용)."""

    YEOGI = "餘氣"  # 여기
    JUNGGI = "中氣"  # 중기
    JEONGGI = "正氣"  # 정기(본기)


@dataclass(frozen=True, slots=True)
class HiddenStem:
    """지장간 한 원소."""

    gan: str  # 천간(한자)
    stage: StageType
    days: int  # 월률분야 일수


# 지지 → 지장간 (餘氣 → [中氣] → 正氣 순). 일수 합 = 30.
_JIJANGGAN: dict[str, list[HiddenStem]] = {
    "子": [HiddenStem("壬", StageType.YEOGI, 10), HiddenStem("癸", StageType.JEONGGI, 20)],
    "丑": [
        HiddenStem("癸", StageType.YEOGI, 9),
        HiddenStem("辛", StageType.JUNGGI, 3),
        HiddenStem("己", StageType.JEONGGI, 18),
    ],
    "寅": [
        HiddenStem("戊", StageType.YEOGI, 7),
        HiddenStem("丙", StageType.JUNGGI, 7),
        HiddenStem("甲", StageType.JEONGGI, 16),
    ],
    "卯": [HiddenStem("甲", StageType.YEOGI, 10), HiddenStem("乙", StageType.JEONGGI, 20)],
    "辰": [
        HiddenStem("乙", StageType.YEOGI, 9),
        HiddenStem("癸", StageType.JUNGGI, 3),
        HiddenStem("戊", StageType.JEONGGI, 18),
    ],
    "巳": [
        HiddenStem("戊", StageType.YEOGI, 7),
        HiddenStem("庚", StageType.JUNGGI, 7),
        HiddenStem("丙", StageType.JEONGGI, 16),
    ],
    "午": [
        HiddenStem("丙", StageType.YEOGI, 10),
        HiddenStem("己", StageType.JUNGGI, 9),
        HiddenStem("丁", StageType.JEONGGI, 11),
    ],
    "未": [
        HiddenStem("丁", StageType.YEOGI, 9),
        HiddenStem("乙", StageType.JUNGGI, 3),
        HiddenStem("己", StageType.JEONGGI, 18),
    ],
    "申": [
        HiddenStem("戊", StageType.YEOGI, 7),
        HiddenStem("壬", StageType.JUNGGI, 7),
        HiddenStem("庚", StageType.JEONGGI, 16),
    ],
    "酉": [HiddenStem("庚", StageType.YEOGI, 10), HiddenStem("辛", StageType.JEONGGI, 20)],
    "戌": [
        HiddenStem("辛", StageType.YEOGI, 9),
        HiddenStem("丁", StageType.JUNGGI, 3),
        HiddenStem("戊", StageType.JEONGGI, 18),
    ],
    "亥": [
        HiddenStem("戊", StageType.YEOGI, 7),
        HiddenStem("甲", StageType.JUNGGI, 7),
        HiddenStem("壬", StageType.JEONGGI, 16),
    ],
}


def get_jijanggan(ji: str) -> list[HiddenStem]:
    """지지의 지장간 목록을 餘氣→[中氣]→正氣 순으로 반환.

    지지가 아니면 ValueError.
    """
    if ji not in JI_SET:
        raise ValueError(f"유효하지 않은 지지: {ji!r}")
    return list(_JIJANGGAN[ji])


def get_primary_stem(ji: str) -> str:
    """지지의 正氣(본기) 천간을 반환. 지지의 대표 오행 산정에 사용.

    지지가 아니면 ValueError.
    """
    for hidden in get_jijanggan(ji):
        if hidden.stage == StageType.JEONGGI:
            return hidden.gan
    raise ValueError(f"正氣 미정의 지지: {ji!r}")  # pragma: no cover (테이블상 불가)

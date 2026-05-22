"""60갑자(六十甲子) 변환 유틸.

근거: 명리 공통 기초. 천간 10주기 · 지지 12주기가 동시에 진행하여
60에서 한 바퀴를 이룬다(최소공배수 60). 순수 결정론적.

이 모듈은 '날짜 → 일주' 같은 천문 보정이 필요한 계산은 다루지 않는다.
(그것은 jeolgi·solar_time 보정이 끝난 뒤 pillars.py에서 처리.)
여기서는 간지 자체의 순환·조회 연산만 제공한다.
"""

from src.engine.constants import (
    CHUN_GAN,
    GAN_EUMYANG,
    GAN_OHAENG,
    JI_EUMYANG,
    JI_JI,
    JI_OHAENG,
    Eumyang,
    Ohaeng,
)


def gan_index(gan: str) -> int:
    """천간 → 0~9. 천간이 아니면 ValueError."""
    try:
        return CHUN_GAN.index(gan)
    except ValueError:
        raise ValueError(f"유효하지 않은 천간: {gan!r}") from None


def ji_index(ji: str) -> int:
    """지지 → 0~11. 지지가 아니면 ValueError."""
    try:
        return JI_JI.index(ji)
    except ValueError:
        raise ValueError(f"유효하지 않은 지지: {ji!r}") from None


def is_valid_ganji(gan: str, ji: str) -> bool:
    """60갑자에 실제로 존재하는 (천간, 지지) 조합인지.

    천간 index와 지지 index의 음양(짝/홀)이 일치해야만 존재한다.
    (예: 甲子 ○, 甲丑 ✗)
    """
    try:
        gi, ji_i = gan_index(gan), ji_index(ji)
    except ValueError:
        return False
    return (gi % 2) == (ji_i % 2)


def ganji_index(gan: str, ji: str) -> int:
    """(천간, 지지) → 60갑자 index 0~59.

    유효하지 않은 조합이면 ValueError.
    g ≡ idx (mod 10), j ≡ idx (mod 12) 를 만족하는 0~59의 유일한 idx를 찾는다.
    """
    gi, ji_i = gan_index(gan), ji_index(ji)
    for idx in range(60):
        if idx % 10 == gi and idx % 12 == ji_i:
            return idx
    raise ValueError(f"존재하지 않는 간지 조합: {gan}{ji}")


def ganji_by_index(index: int) -> tuple[str, str]:
    """60갑자 index → (천간, 지지). index는 mod 60으로 순환."""
    i = index % 60
    return CHUN_GAN[i % 10], JI_JI[i % 12]


def next_ganji(gan: str, ji: str, step: int = 1) -> tuple[str, str]:
    """현재 간지에서 step 칸 이동한 간지 (60 순환). step 음수 가능."""
    return ganji_by_index(ganji_index(gan, ji) + step)


def gan_ohaeng(gan: str) -> Ohaeng:
    if gan not in GAN_OHAENG:
        raise ValueError(f"유효하지 않은 천간: {gan!r}")
    return GAN_OHAENG[gan]


def ji_ohaeng(ji: str) -> Ohaeng:
    if ji not in JI_OHAENG:
        raise ValueError(f"유효하지 않은 지지: {ji!r}")
    return JI_OHAENG[ji]


def gan_eumyang(gan: str) -> Eumyang:
    if gan not in GAN_EUMYANG:
        raise ValueError(f"유효하지 않은 천간: {gan!r}")
    return GAN_EUMYANG[gan]


def ji_eumyang(ji: str) -> Eumyang:
    if ji not in JI_EUMYANG:
        raise ValueError(f"유효하지 않은 지지: {ji!r}")
    return JI_EUMYANG[ji]

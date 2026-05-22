"""명리 기초 상수 — 천간·지지·오행·음양·60갑자.

근거: 명리 공통 기초 (연해자평·자평진전 등 모든 고전 공통).
순수 결정론적 테이블. 같은 입력 → 항상 같은 출력.

한자(원문)를 정본(canonical)으로 두고, romanization은 코드 식별자로 사용한다.
사용자 노출 텍스트는 한글 원본을 따로 둔다.
"""

from enum import StrEnum


class Ohaeng(StrEnum):
    """오행(五行)."""

    MOK = "木"  # 목 (나무)
    HWA = "火"  # 화 (불)
    TO = "土"  # 토 (흙)
    GEUM = "金"  # 금 (쇠)
    SU = "水"  # 수 (물)


class Eumyang(StrEnum):
    """음양(陰陽)."""

    YANG = "陽"  # 양 (+)
    EUM = "陰"  # 음 (-)


# ── 천간(天干) 10 ─────────────────────────────────────────────
# 순서 고정: 갑을병정무기경신임계
CHUN_GAN: tuple[str, ...] = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")

CHUN_GAN_ROMAN: dict[str, str] = {
    "甲": "gap",
    "乙": "eul",
    "丙": "byeong",
    "丁": "jeong",
    "戊": "mu",
    "己": "gi",
    "庚": "gyeong",
    "辛": "sin",
    "壬": "im",
    "癸": "gye",
}

CHUN_GAN_HANGUL: dict[str, str] = {
    "甲": "갑",
    "乙": "을",
    "丙": "병",
    "丁": "정",
    "戊": "무",
    "己": "기",
    "庚": "경",
    "辛": "신",
    "壬": "임",
    "癸": "계",
}

GAN_OHAENG: dict[str, Ohaeng] = {
    "甲": Ohaeng.MOK,
    "乙": Ohaeng.MOK,
    "丙": Ohaeng.HWA,
    "丁": Ohaeng.HWA,
    "戊": Ohaeng.TO,
    "己": Ohaeng.TO,
    "庚": Ohaeng.GEUM,
    "辛": Ohaeng.GEUM,
    "壬": Ohaeng.SU,
    "癸": Ohaeng.SU,
}

# 양간: 갑병무경임 / 음간: 을정기신계
GAN_EUMYANG: dict[str, Eumyang] = {
    g: (Eumyang.YANG if i % 2 == 0 else Eumyang.EUM) for i, g in enumerate(CHUN_GAN)
}


# ── 지지(地支) 12 ─────────────────────────────────────────────
# 순서 고정: 자축인묘진사오미신유술해
JI_JI: tuple[str, ...] = (
    "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥",
)

JI_JI_ROMAN: dict[str, str] = {
    "子": "ja",
    "丑": "chuk",
    "寅": "in",
    "卯": "myo",
    "辰": "jin",
    "巳": "sa",
    "午": "o",
    "未": "mi",
    "申": "sin",
    "酉": "yu",
    "戌": "sul",
    "亥": "hae",
}

JI_JI_HANGUL: dict[str, str] = {
    "子": "자",
    "丑": "축",
    "寅": "인",
    "卯": "묘",
    "辰": "진",
    "巳": "사",
    "午": "오",
    "未": "미",
    "申": "신",
    "酉": "유",
    "戌": "술",
    "亥": "해",
}

# 지지 본기(本氣) 오행 — 지장간 정기 기준
# 인묘=목, 사오=화, 진술축미=토, 신유=금, 해자=수
JI_OHAENG: dict[str, Ohaeng] = {
    "寅": Ohaeng.MOK,
    "卯": Ohaeng.MOK,
    "巳": Ohaeng.HWA,
    "午": Ohaeng.HWA,
    "辰": Ohaeng.TO,
    "戌": Ohaeng.TO,
    "丑": Ohaeng.TO,
    "未": Ohaeng.TO,
    "申": Ohaeng.GEUM,
    "酉": Ohaeng.GEUM,
    "亥": Ohaeng.SU,
    "子": Ohaeng.SU,
}

# 지지 음양 (전통 배속): 자인진오신술=양, 축묘사미유해=음
JI_EUMYANG: dict[str, Eumyang] = {
    j: (Eumyang.YANG if i % 2 == 0 else Eumyang.EUM) for i, j in enumerate(JI_JI)
}

# 지지가 대응하는 띠(생초)/시각 참고용은 추후 모듈에서.


# ── 60갑자(六十甲子) ──────────────────────────────────────────
# index 0 = 甲子, 1 = 乙丑, ... 59 = 癸亥.
# 천간은 10주기, 지지는 12주기로 동시에 진행 → 60에서 한 바퀴.
GANJI_60: tuple[str, ...] = tuple(
    CHUN_GAN[i % 10] + JI_JI[i % 12] for i in range(60)
)

# 한자 집합 (검증용)
GAN_SET = frozenset(CHUN_GAN)
JI_SET = frozenset(JI_JI)

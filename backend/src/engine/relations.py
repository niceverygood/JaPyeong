"""합·충·형·해·파 — 천간/지지 간 관계 분석.

근거: 명리 공통 조합표. 합화(合化) 성립 판정은 학설 차가 커서 분리하고,
이 모듈에서는 '관계의 성립(짝/조 매칭)'만 결정론적으로 검출한다.

default 처리 (학설 차 명시):
- 삼합/방합: 3자 완전 성립만 검출. 반합(2자)·암합은 비검출.
  TODO(policy): 반합 채택 여부는 자문위원 결정 필요.
- 형(刑): 삼형(寅巳申·丑戌未) 3자 완전, 상형(子卯) 2자, 자형(辰辰·午午·酉酉·亥亥)만.
  부분 삼형(2자)은 비검출. TODO(policy): 부분 형 채택 여부 자문위원 결정.
- 합화(合化) 성립: 미구현(detect_hap_hwa → NotImplementedError).

신살(귀인·역마 등)은 이 모듈이 다루지 않는다(별도 모듈, policy 항목 9).

순수 결정론적: 같은 입력 → 항상 같은 출력.
"""

from dataclasses import dataclass
from enum import StrEnum
from itertools import combinations
from typing import NoReturn

from src.engine.schema import FourPillars


class RelationType(StrEnum):
    """관계 종류. 값은 한글(사용자 노출용)."""

    CHEON_GAN_HAP = "천간합"  # 天干合
    JI_JI_YUK_HAP = "육합"  # 六合
    JI_JI_SAM_HAP = "삼합"  # 三合
    JI_JI_BANG_HAP = "방합"  # 方合
    JI_JI_CHUNG = "충"  # 沖
    JI_JI_HYEONG = "형"  # 刑
    JI_JI_HAE = "해"  # 害
    JI_JI_PA = "파"  # 破


@dataclass(frozen=True, slots=True)
class Relation:
    """검출된 관계 1건."""

    type: RelationType
    members: tuple[str, ...]  # 한자 글자 (위치 순서)
    positions: tuple[str, ...]  # year_gan / month_ji / day_ji ...


_POSITIONS = ("year", "month", "day", "hour")
_POS_INDEX = {p: i for i, p in enumerate(_POSITIONS)}

# ── 조합표 (frozenset) ───────────────────────────────────────
def _fs(*pairs: tuple[str, ...]) -> list[frozenset[str]]:
    return [frozenset(p) for p in pairs]


_CHEON_GAN_HAP = _fs(("甲", "己"), ("乙", "庚"), ("丙", "辛"), ("丁", "壬"), ("戊", "癸"))
_YUK_HAP = _fs(("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未"))
_CHUNG = _fs(("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥"))
_HAE = _fs(("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌"))
_PA = _fs(("子", "酉"), ("卯", "午"), ("巳", "申"), ("寅", "亥"), ("丑", "辰"), ("戌", "未"))
_SANG_HYEONG = _fs(("子", "卯"))  # 상형 (2자)

_SAM_HAP = _fs(("申", "子", "辰"), ("亥", "卯", "未"), ("寅", "午", "戌"), ("巳", "酉", "丑"))
_BANG_HAP = _fs(("寅", "卯", "辰"), ("巳", "午", "未"), ("申", "酉", "戌"), ("亥", "子", "丑"))
_SAM_HYEONG = _fs(("寅", "巳", "申"), ("丑", "戌", "未"))  # 삼형 (3자)

_JA_HYEONG = frozenset(("辰", "午", "酉", "亥"))  # 자형

# 합(合) 계열 타입 (has_hap 판정용)
_HAP_TYPES = frozenset(
    {
        RelationType.CHEON_GAN_HAP,
        RelationType.JI_JI_YUK_HAP,
        RelationType.JI_JI_SAM_HAP,
        RelationType.JI_JI_BANG_HAP,
    }
)


def _components(pillars: FourPillars, kind: str) -> list[tuple[str, str]]:
    """(position_label, 글자) 목록. kind='gan' 또는 'ji'. 시주 없으면 제외."""
    out: list[tuple[str, str]] = []
    for pos in _POSITIONS:
        pillar = getattr(pillars, pos, None)
        if pillar is None:
            continue
        out.append((f"{pos}_{kind}", pillar.gan if kind == "gan" else pillar.ji))
    return out


def _pos_sort(item: tuple[str, str]) -> int:
    return _POS_INDEX[item[0].rsplit("_", 1)[0]]


def _scan_pairs(
    items: list[tuple[str, str]],
    tables: list[tuple[list[frozenset[str]], RelationType]],
) -> list[Relation]:
    found: list[Relation] = []
    for c1, c2 in combinations(items, 2):
        if c1[1] == c2[1]:
            continue  # 동일 글자 짝은 자형 스캐너가 처리
        pair = frozenset((c1[1], c2[1]))
        ordered = sorted((c1, c2), key=_pos_sort)
        for table, rtype in tables:
            if pair in table:
                found.append(
                    Relation(rtype, tuple(c[1] for c in ordered), tuple(c[0] for c in ordered))
                )
    return found


def _scan_self_hyeong(items: list[tuple[str, str]]) -> list[Relation]:
    found: list[Relation] = []
    for c1, c2 in combinations(items, 2):
        if c1[1] == c2[1] and c1[1] in _JA_HYEONG:
            ordered = sorted((c1, c2), key=_pos_sort)
            found.append(
                Relation(
                    RelationType.JI_JI_HYEONG,
                    tuple(c[1] for c in ordered),
                    tuple(c[0] for c in ordered),
                )
            )
    return found


def _scan_triples(
    items: list[tuple[str, str]],
    tables: list[tuple[list[frozenset[str]], RelationType]],
) -> list[Relation]:
    found: list[Relation] = []
    for trio in combinations(items, 3):
        chars = frozenset(c[1] for c in trio)
        if len(chars) != 3:
            continue  # 같은 글자 포함 조합은 완전 삼합/삼형 아님
        ordered = sorted(trio, key=_pos_sort)
        for table, rtype in tables:
            if chars in table:
                found.append(
                    Relation(rtype, tuple(c[1] for c in ordered), tuple(c[0] for c in ordered))
                )
    return found


def find_all_relations(pillars: FourPillars) -> list[Relation]:
    """사주 내 모든 합충형해파 관계를 검출."""
    gans = _components(pillars, "gan")
    jis = _components(pillars, "ji")

    out: list[Relation] = []
    out += _scan_pairs(gans, [(_CHEON_GAN_HAP, RelationType.CHEON_GAN_HAP)])
    out += _scan_pairs(
        jis,
        [
            (_YUK_HAP, RelationType.JI_JI_YUK_HAP),
            (_CHUNG, RelationType.JI_JI_CHUNG),
            (_HAE, RelationType.JI_JI_HAE),
            (_PA, RelationType.JI_JI_PA),
            (_SANG_HYEONG, RelationType.JI_JI_HYEONG),
        ],
    )
    out += _scan_self_hyeong(jis)
    out += _scan_triples(
        jis,
        [
            (_SAM_HAP, RelationType.JI_JI_SAM_HAP),
            (_BANG_HAP, RelationType.JI_JI_BANG_HAP),
            (_SAM_HYEONG, RelationType.JI_JI_HYEONG),
        ],
    )
    return out


def find_relations_by_type(pillars: FourPillars, relation_type: RelationType) -> list[Relation]:
    """특정 종류의 관계만 반환."""
    return [r for r in find_all_relations(pillars) if r.type == relation_type]


def has_chung(pillars: FourPillars, position: str) -> bool:
    """해당 위치(예: 'year_ji')가 충에 가담하는지."""
    return any(
        position in r.positions
        for r in find_relations_by_type(pillars, RelationType.JI_JI_CHUNG)
    )


def has_hap(pillars: FourPillars, position: str) -> bool:
    """해당 위치가 합(천간합·육합·삼합·방합) 중 하나에 가담하는지."""
    return any(
        position in r.positions and r.type in _HAP_TYPES
        for r in find_all_relations(pillars)
    )


def detect_hap_hwa(pillars: FourPillars, hap: Relation) -> NoReturn:
    """합화(合化) 성립 판정. 학설 차가 큼(월령·천간 투출·일간 영향 등).

    현재 미구현.
    TODO(policy): myeongri-policy.md 항목 13(합화 성립 기준)으로 추가 검토 필요.
    """
    raise NotImplementedError(
        "합화(合化) 성립 판정은 미구현 — 학설 차 큼. myeongri-policy.md 항목 추가 후 구현."
    )

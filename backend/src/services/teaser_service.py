"""전환용 무료 맛보기(teaser) — 결정론 명식에서 즉시 생성(LLM 비용 0).

목적: '나에 대한 정확한 한 줄'을 무료로 보여 트러스트를 만들고, 전체(LLM) 풀이는
잠금해 결제로 잇는다. 공포·단정 톤 금지(자평 가드레일) — '성향/흐름'으로만 표현.
입력은 saju_service.analyze_natal 출력 dict, 출력은 사람이 읽는 한국어 문자열들.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# 일간 오행(한자) → 본성 한 줄
_ELEMENT_NATURE: dict[str, str] = {
    "木": "성장과 기획의",
    "火": "열정과 표현의",
    "土": "안정과 중재의",
    "金": "결단과 원칙의",
    "水": "지혜와 유연함의",
}

# 강약 → 성향 수식
_STRENGTH_TRAIT: dict[str, str] = {
    "신강": "추진력이 강한",
    "신약": "신중하고 섬세한",
    "중화": "균형이 잡힌",
}

# 십성 키 → (한글, 짧은 태그)
_TEN_GOD_TRAIT: dict[str, tuple[str, str]] = {
    "bi_gyeon": ("비견", "자립·주관"),
    "gyeop_jae": ("겁재", "추진·승부"),
    "sik_sin": ("식신", "표현·여유"),
    "sang_gwan": ("상관", "재능·자유"),
    "jeong_jae": ("정재", "성실·관리"),
    "pyeon_jae": ("편재", "수완·기회"),
    "jeong_gwan": ("정관", "책임·원칙"),
    "pyeon_gwan": ("편관", "결단·돌파"),
    "jeong_in": ("정인", "안정·사려"),
    "pyeon_in": ("편인", "통찰·독창"),
}

_LABEL_FLOW: dict[str, str] = {
    "대길": "기운이 크게 트이는",
    "길": "순조롭게 흐르는",
    "평": "차분히 다지는",
    "주의": "한 박자 살피며 가는",
    "흉": "무리를 피하고 내실을 다지는",
}


def _strongest_ten_god(ten_gods: dict[str, Any]) -> tuple[str, str] | None:
    items = [(k, int(v or 0)) for k, v in (ten_gods or {}).items() if k in _TEN_GOD_TRAIT]
    if not items:
        return None
    best = max(items, key=lambda x: x[1])
    if best[1] <= 0:
        return None
    return _TEN_GOD_TRAIT[best[0]]


def personal_hook(natal: dict[str, Any]) -> str:
    """무료 '내 한 줄' — 일간 오행 + 강약 + 대표 십성 성향. 항상 즉시·정확."""
    dm = str(natal.get("day_master", "")).strip()
    elem = str(natal.get("day_master_element", "")).strip()
    nature = _ELEMENT_NATURE.get(elem, "고유한")
    strength = ((natal.get("strength") or {}).get("label") or "").strip()
    trait = _STRENGTH_TRAIT.get(strength, "")
    sg = _strongest_ten_god(natal.get("ten_gods") or {})

    head = f"{dm}{elem} 일간".strip()
    body = f"{nature} 바탕에 {trait} 성향".strip()
    line = f"{head} — {body}".replace("  ", " ")
    if sg:
        line += f". 대표 기운은 {sg[0]}({sg[1]})."
    return line


def current_flow(natal: dict[str, Any], birth_year: int | None) -> str:
    """현재 대운 흐름 한 줄 — life_flow 에서 현재 나이 구간을 찾아 표현."""
    flow = natal.get("life_flow") or []
    if not flow or not birth_year:
        return ""
    age = datetime.now(UTC).year - int(birth_year)
    cur = None
    for p in flow:
        try:
            if int(p.get("start_age", -1)) <= age <= int(p.get("end_age", -1)):
                cur = p
                break
        except (TypeError, ValueError):
            continue
    if cur is None:
        return ""
    label = str(cur.get("label", "")).strip()
    phrase = _LABEL_FLOW.get(label, "흐르는")
    gz = f"{cur.get('gan', '')}{cur.get('ji', '')}"
    return f"지금({age}세 무렵)은 {phrase} {gz} 대운 구간입니다."


_CATEGORY_COVERS: dict[str, list[str]] = {
    "love": ["인연이 들고 나는 시기", "관계에서 살릴 점과 조심할 점", "당신 사주에 맞는 만남의 결"],
    "career": ["이동·전환에 유리한 시기", "지금 자리에서 키울 강점", "분야와 방식의 결"],
    "money": ["재물이 모이고 흩어지는 흐름", "확장과 수성의 시기", "당신에게 맞는 재물의 방식"],
    "default": ["올해·내년의 핵심 시기", "조심할 시기와 살릴 시기", "당신 사주에 맞는 구체적 조언"],
}


def covers_for(question: str | None) -> list[str]:
    """전체 풀이가 무엇을 짚어줄지 — 결제 동기. 질문 키워드로 카테고리 추정."""
    q = (question or "").lower()
    cat = "default"
    if any(w in q for w in ["연애", "결혼", "사랑", "이성", "인연", "배우자"]):
        cat = "love"
    elif any(w in q for w in ["직업", "이직", "취업", "사업", "창업", "커리어", "진로"]):
        cat = "career"
    elif any(w in q for w in ["돈", "재물", "투자", "재정", "money"]):
        cat = "money"
    covers = list(_CATEGORY_COVERS[cat])
    covers.append("연해자평·삼명통회 등 고전 근거")
    return covers


def build_teaser(
    natal: dict[str, Any],
    question: str | None = None,
    birth_year: int | None = None,
) -> dict[str, Any]:
    """무료 맛보기 묶음 — 결제 전 보여줄 hook/flow/covers."""
    return {
        "hook": personal_hook(natal),
        "flow": current_flow(natal, birth_year),
        "covers": covers_for(question),
        "note": "맛보기는 명식에서 즉시 계산한 결과입니다. 전체 풀이는 AI가 고전 근거와 함께 깊이 있게 짚어 드립니다.",
    }

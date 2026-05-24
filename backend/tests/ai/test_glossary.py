"""glossary.annotate_hanja 단위 테스트.

규칙:
1) 단어 매핑이 있으면 단어 단위로 '한글(漢字)' 변환
2) 단어 매핑이 없으면 글자 단위로 변환해 한 단어로 묶어 표기
3) 이미 '한글(한자)' 패턴은 보존(중복 방지)
4) 한자가 없으면 입력 그대로
"""

from __future__ import annotations

import pytest

from src.ai.glossary import annotate_hanja


def test_empty_and_no_hanja() -> None:
    assert annotate_hanja("") == ""
    assert annotate_hanja("순한글 문장입니다.") == "순한글 문장입니다."


def test_term_mapping_wins() -> None:
    """단어 사전이 있는 한자는 단어 단위 변환."""
    out = annotate_hanja("正官이 강하다")
    assert out == "정관(正官)이 강하다"


def test_char_fallback_when_no_term() -> None:
    """단어 사전에 없으면 글자별로 묶어 한 단어로 표기."""
    # '甲木'은 단어 사전에 없음 → 글자 변환 후 '갑목(甲木)'
    out = annotate_hanja("甲木이 천간에 있다")
    assert "갑목(甲木)" in out


def test_preserves_already_annotated() -> None:
    """이미 '한글(한자)' 형식은 보존 (중복 방지)."""
    src = "정관(正官)이 강하고 偏財도 있다"
    out = annotate_hanja(src)
    # 정관(正官)은 그대로
    assert "정관(正官)" in out
    # 중복 변환 금지: 정관(正官)(正官) 같은 패턴 없음
    assert "(正官)(正官)" not in out
    # 새로운 偏財는 편재(偏財)로 변환
    assert "편재(偏財)" in out


def test_multiple_terms_in_one_sentence() -> None:
    out = annotate_hanja("食神格에 用神은 印星")
    assert "식신격(食神格)" in out
    assert "용신(用神)" in out
    assert "인성(印星)" in out


def test_chung_pair() -> None:
    """충 6쌍 단어 매핑."""
    out = annotate_hanja("亥巳沖이 보인다")
    assert "해사충(亥巳沖)" in out


def test_unknown_hanja_kept_in_token() -> None:
    """모르는 한자는 그대로 두되, 알려진 글자가 하나라도 있으면 묶어 변환."""
    # '木龍' — 龍은 사전 없음. 木은 있음 → '목龍(木龍)'
    out = annotate_hanja("木龍")
    assert out == "목龍(木龍)"


def test_pure_unknown_hanja_untouched() -> None:
    """모든 글자가 사전에 없으면 변환하지 않음."""
    # '龍鳳'은 둘 다 사전 없음 → 그대로
    assert annotate_hanja("龍鳳이 있다") == "龍鳳이 있다"


def test_term_longer_than_char_priority() -> None:
    """긴 단어가 글자별 변환보다 우선."""
    # '正官格'은 '正官'+'格'으로 쪼개지지 않고 한 단어로 매칭되어야 함
    out = annotate_hanja("正官格")
    assert out == "정관격(正官格)"
    # 변환된 결과에 '정관(正官)격' 같은 중첩 형태가 없어야 함
    assert "정관(正官)" not in out


def test_mixed_with_korean_around() -> None:
    out = annotate_hanja("그의 日柱는 丙申으로 보인다")
    assert "일주(日柱)" in out
    # 丙申은 단어 사전 없음 → 병신(丙申)
    assert "병신(丙申)" in out


def test_no_modification_when_only_pre_annotated() -> None:
    src = "용신(用神)과 격국(格局)을 본다"
    assert annotate_hanja(src) == src


@pytest.mark.parametrize(
    "text",
    [
        "甲乙丙丁",  # 천간 4개 연속
        "子午沖과 卯酉沖",
        "印星·比劫·食傷·財星·官星",
    ],
)
def test_complex_strings_dont_throw(text: str) -> None:
    out = annotate_hanja(text)
    # 변환 후에는 어떤 식으로든 '(' 가 포함되거나 원본 한자가 살아 있어야 함
    assert "(" in out or out == text

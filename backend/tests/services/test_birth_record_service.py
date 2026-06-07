"""services.birth_record_service 단위 테스트."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet, MultiFernet

from src.engine.schema import BirthInfo
from src.security.pii_encryption import PIIEncryptionError
from src.services.birth_record_service import (
    decrypt_birth,
    decrypt_birth_to_pillars,
    encrypt_birth,
    safe_decrypt_to_pillars,
)


@pytest.fixture
def fernet() -> MultiFernet:
    return MultiFernet([Fernet(Fernet.generate_key())])


@pytest.fixture
def birth() -> BirthInfo:
    """1990-05-20 14:30 양력, 서울 좌표 — 사주 분석 가능."""
    return BirthInfo(
        name="홍길동",
        gender="M",
        calendar="solar",
        year=1990, month=5, day=20,
        hour=14, minute=30,
        is_leap_month=False,
        birth_place="서울",
        longitude=126.9784,
        latitude=37.5665,
        timezone="Asia/Seoul",
    )


# ── Round-trip ───────────────────────────────────────────
def test_encrypt_decrypt_roundtrip(fernet: MultiFernet, birth: BirthInfo) -> None:
    blob = encrypt_birth(birth, fernet=fernet)
    restored = decrypt_birth(blob, fernet=fernet)
    assert restored == birth


def test_encrypted_blob_is_bytes(fernet: MultiFernet, birth: BirthInfo) -> None:
    blob = encrypt_birth(birth, fernet=fernet)
    assert isinstance(blob, bytes)
    assert len(blob) > 100  # 의미 있는 크기


def test_roundtrip_minimal_birth(fernet: MultiFernet) -> None:
    """이름·좌표 없는 최소 BirthInfo도 round-trip."""
    minimal = BirthInfo(
        gender="F",
        year=2000, month=1, day=1,
    )
    blob = encrypt_birth(minimal, fernet=fernet)
    restored = decrypt_birth(blob, fernet=fernet)
    assert restored == minimal


# ── End-to-end: bytes → FourPillars ──────────────────────
def test_decrypt_to_pillars(fernet: MultiFernet, birth: BirthInfo) -> None:
    """bytes → BirthInfo → FourPillars 풀 변환."""
    blob = encrypt_birth(birth, fernet=fernet)
    pillars = decrypt_birth_to_pillars(blob, fernet=fernet)
    # 사주 8자 (천간 + 지지) 검증 — 결정론적 결과
    assert pillars.day.gan in {"甲","乙","丙","丁","戊","己","庚","辛","壬","癸"}
    assert pillars.day.ji in {"子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"}
    assert pillars.year is not None
    assert pillars.hour is not None


# ── safe_decrypt: 예외 swallow ───────────────────────────
def test_safe_decrypt_returns_pillars_on_success(
    fernet: MultiFernet, birth: BirthInfo,
) -> None:
    blob = encrypt_birth(birth, fernet=fernet)
    result = safe_decrypt_to_pillars(blob, fernet=fernet)
    assert result is not None
    assert result.day.gan


def test_safe_decrypt_returns_none_on_wrong_key(birth: BirthInfo) -> None:
    """다른 키로 암호화된 blob → safe 함수는 None 반환."""
    encrypt_fernet = MultiFernet([Fernet(Fernet.generate_key())])
    decrypt_fernet = MultiFernet([Fernet(Fernet.generate_key())])
    blob = encrypt_birth(birth, fernet=encrypt_fernet)
    assert safe_decrypt_to_pillars(blob, fernet=decrypt_fernet) is None


def test_safe_decrypt_returns_none_on_tampered(
    fernet: MultiFernet, birth: BirthInfo,
) -> None:
    blob = encrypt_birth(birth, fernet=fernet)
    tampered = blob[:-1] + bytes([blob[-1] ^ 0xFF])
    assert safe_decrypt_to_pillars(tampered, fernet=fernet) is None


def test_safe_decrypt_returns_none_on_empty() -> None:
    """empty bytes — safe는 None."""
    fernet = MultiFernet([Fernet(Fernet.generate_key())])
    assert safe_decrypt_to_pillars(b"", fernet=fernet) is None


# ── strict 모드 — 예외 raise ──────────────────────────────
def test_strict_decrypt_raises_on_wrong_key(birth: BirthInfo) -> None:
    encrypt_fernet = MultiFernet([Fernet(Fernet.generate_key())])
    decrypt_fernet = MultiFernet([Fernet(Fernet.generate_key())])
    blob = encrypt_birth(birth, fernet=encrypt_fernet)
    with pytest.raises(PIIEncryptionError):
        decrypt_birth_to_pillars(blob, fernet=decrypt_fernet)


def test_strict_decrypt_raises_on_invalid_payload(fernet: MultiFernet) -> None:
    """복호화는 성공했으나 BirthInfo 스키마 위반 → pydantic 에러."""
    from src.security.pii_encryption import encrypt_pii
    bad = encrypt_pii({"year": "not-a-number"}, fernet=fernet)
    with pytest.raises((ValueError, TypeError, Exception)):
        decrypt_birth(bad, fernet=fernet)


def test_safe_decrypt_returns_none_on_invalid_payload(fernet: MultiFernet) -> None:
    """safe 버전은 스키마 위반도 None."""
    from src.security.pii_encryption import encrypt_pii
    bad = encrypt_pii({"year": "not-a-number"}, fernet=fernet)
    assert safe_decrypt_to_pillars(bad, fernet=fernet) is None


# ── 한글 / 한자 PII 보존 ─────────────────────────────────
def test_korean_name_preserved(fernet: MultiFernet) -> None:
    """한글 이름·장소 round-trip."""
    b = BirthInfo(
        name="김자평",
        gender="F",
        year=1985, month=12, day=25,
        birth_place="부산광역시",
    )
    blob = encrypt_birth(b, fernet=fernet)
    restored = decrypt_birth(blob, fernet=fernet)
    assert restored.name == "김자평"
    assert restored.birth_place == "부산광역시"

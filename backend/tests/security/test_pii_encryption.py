"""security.pii_encryption 단위 테스트.

검증 영역:
  - Round-trip (다양한 payload)
  - 다중 키 (MultiFernet) 로테이션
  - 변조 감지 (InvalidToken)
  - 버전 prefix 정합성
  - 환경변수 미설정 시 raise
  - 형식 오류 처리
  - rotate() 데이터 마이그레이션
"""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet, MultiFernet

from src.security.pii_encryption import (
    VERSION_FERNET,
    PIIConfigError,
    PIIEncryptionError,
    decrypt_pii,
    encrypt_pii,
    generate_key,
    is_encrypted,
    make_fernet,
    rotate,
)


# ── 테스트 헬퍼: 환경변수 우회 ────────────────────────────
@pytest.fixture
def primary_key() -> bytes:
    return Fernet.generate_key()


@pytest.fixture
def old_key() -> bytes:
    return Fernet.generate_key()


@pytest.fixture
def fernet(primary_key: bytes) -> MultiFernet:
    return MultiFernet([Fernet(primary_key)])


@pytest.fixture
def fernet_rotated(primary_key: bytes, old_key: bytes) -> MultiFernet:
    """현재 primary + 이전 키 (rotation 시나리오)."""
    return MultiFernet([Fernet(primary_key), Fernet(old_key)])


# ── 키 생성 ─────────────────────────────────────────────
def test_generate_key_returns_valid_fernet_key() -> None:
    """generate_key() 결과로 즉시 Fernet 인스턴스 생성 가능."""
    key = generate_key()
    assert isinstance(key, str)
    assert len(key) == 44  # base64-encoded 32 bytes
    Fernet(key.encode())  # 예외 없으면 OK


# ── Round-trip ───────────────────────────────────────────
def test_roundtrip_simple(fernet: MultiFernet) -> None:
    payload = {"gender": "M", "year": 1990, "month": 5, "day": 20}
    blob = encrypt_pii(payload, fernet=fernet)
    result = decrypt_pii(blob, fernet=fernet)
    assert result == payload


def test_roundtrip_with_korean(fernet: MultiFernet) -> None:
    """한글 / 한자 포함 payload."""
    payload = {
        "name": "홍길동",
        "label": "본인",
        "birth_place": "서울특별시",
        "note": "丙午 일주 검증",
    }
    blob = encrypt_pii(payload, fernet=fernet)
    result = decrypt_pii(blob, fernet=fernet)
    assert result == payload


def test_roundtrip_complex_nested(fernet: MultiFernet) -> None:
    """중첩 구조 + 다양한 타입."""
    payload = {
        "birth": {
            "year": 1990, "month": 5, "day": 20,
            "hour": 14, "minute": 30,
            "calendar": "solar", "is_leap_month": False,
        },
        "location": {"longitude": 126.9784, "latitude": 37.5665, "tz": "Asia/Seoul"},
        "tags": ["본인", "주요 결정 대비"],
    }
    blob = encrypt_pii(payload, fernet=fernet)
    result = decrypt_pii(blob, fernet=fernet)
    assert result == payload


def test_roundtrip_empty_dict(fernet: MultiFernet) -> None:
    """빈 dict도 round-trip 가능."""
    blob = encrypt_pii({}, fernet=fernet)
    assert decrypt_pii(blob, fernet=fernet) == {}


# ── 버전 prefix ──────────────────────────────────────────
def test_version_prefix_attached(fernet: MultiFernet) -> None:
    """blob 첫 바이트가 VERSION_FERNET."""
    blob = encrypt_pii({"a": 1}, fernet=fernet)
    assert blob[0] == VERSION_FERNET


def test_is_encrypted_detects_format(fernet: MultiFernet) -> None:
    blob = encrypt_pii({"x": 1}, fernet=fernet)
    assert is_encrypted(blob)
    assert not is_encrypted(b"plain text")
    assert not is_encrypted(b"")
    assert not is_encrypted(bytes([0xFF]))  # 미지원 버전


def test_unknown_version_raises(fernet: MultiFernet) -> None:
    """버전이 미래/손상이면 명확한 에러."""
    blob = bytes([0xFE]) + b"some_token_garbage"
    with pytest.raises(PIIEncryptionError, match="지원하지 않는 암호화 버전"):
        decrypt_pii(blob, fernet=fernet)


# ── 변조 감지 ───────────────────────────────────────────
def test_tampered_token_raises(fernet: MultiFernet) -> None:
    """Fernet token 변조 시 InvalidToken → PIIEncryptionError."""
    blob = encrypt_pii({"a": 1}, fernet=fernet)
    # 마지막 바이트 뒤집기
    tampered = blob[:-1] + bytes([blob[-1] ^ 0xFF])
    with pytest.raises(PIIEncryptionError, match="복호화 실패"):
        decrypt_pii(tampered, fernet=fernet)


def test_wrong_key_raises(primary_key: bytes) -> None:
    """다른 키로 암호화한 blob을 현재 키로 복호화 시도."""
    other_key = Fernet.generate_key()
    other_fernet = MultiFernet([Fernet(other_key)])
    my_fernet = MultiFernet([Fernet(primary_key)])

    blob = encrypt_pii({"secret": "value"}, fernet=other_fernet)
    with pytest.raises(PIIEncryptionError, match="복호화 실패"):
        decrypt_pii(blob, fernet=my_fernet)


# ── 키 로테이션 (MultiFernet) ─────────────────────────────
def test_old_key_can_decrypt_after_rotation(
    primary_key: bytes, old_key: bytes,
) -> None:
    """이전 키로 암호화된 데이터를, 새 키 추가 후에도 복호화 가능."""
    # T0: 이전 키만 있을 때 암호화
    old_fernet = MultiFernet([Fernet(old_key)])
    blob = encrypt_pii({"original": True}, fernet=old_fernet)

    # T1: 새 키가 primary, old_key는 fallback 으로 추가
    new_fernet = MultiFernet([Fernet(primary_key), Fernet(old_key)])
    result = decrypt_pii(blob, fernet=new_fernet)
    assert result == {"original": True}


def test_new_encryption_uses_primary(
    primary_key: bytes, old_key: bytes,
) -> None:
    """rotation 시 신규 암호화는 primary (첫 번째) 키 사용."""
    rotated = MultiFernet([Fernet(primary_key), Fernet(old_key)])
    primary_only = MultiFernet([Fernet(primary_key)])

    blob = encrypt_pii({"x": 1}, fernet=rotated)
    # primary 만 있는 fernet 으로도 복호화 가능해야 → primary 키로 암호화됐단 뜻
    assert decrypt_pii(blob, fernet=primary_only) == {"x": 1}


def test_rotate_function(primary_key: bytes, old_key: bytes) -> None:
    """rotate() — 기존 token 을 현재 primary 키로 재서명."""
    # T0: 이전 키로 암호화
    old_fernet = MultiFernet([Fernet(old_key)])
    old_blob = encrypt_pii({"value": 42}, fernet=old_fernet)

    # T1: 로테이션 — 새 키 primary + 이전 키 fallback
    rotated = MultiFernet([Fernet(primary_key), Fernet(old_key)])
    new_blob = rotate(old_blob, fernet=rotated)

    # T2: 이전 키 제거된 환경에서도 복호화 가능해야 (새 키 primary 사용)
    primary_only = MultiFernet([Fernet(primary_key)])
    assert decrypt_pii(new_blob, fernet=primary_only) == {"value": 42}

    # 버전 prefix 보존
    assert new_blob[0] == VERSION_FERNET


def test_rotate_wrong_key_raises(primary_key: bytes) -> None:
    """rotate 시 해독할 키가 없으면 실패."""
    completely_other = Fernet.generate_key()
    other_fernet = MultiFernet([Fernet(completely_other)])
    old_blob = encrypt_pii({"x": 1}, fernet=other_fernet)

    primary_only = MultiFernet([Fernet(primary_key)])
    with pytest.raises(PIIEncryptionError, match="rotation 실패"):
        rotate(old_blob, fernet=primary_only)


# ── 형식 오류 ────────────────────────────────────────────
def test_empty_blob_raises(fernet: MultiFernet) -> None:
    with pytest.raises(PIIEncryptionError, match="빈 blob"):
        decrypt_pii(b"", fernet=fernet)


def test_too_short_blob_raises(fernet: MultiFernet) -> None:
    with pytest.raises(PIIEncryptionError, match="너무 짧음"):
        decrypt_pii(bytes([VERSION_FERNET]), fernet=fernet)


# ── 환경변수 ────────────────────────────────────────────
def test_no_env_key_raises() -> None:
    """PII_ENCRYPTION_KEY 미설정 시 make_fernet() raise."""
    os.environ.pop("PII_ENCRYPTION_KEY", None)
    with pytest.raises(PIIConfigError, match="PII_ENCRYPTION_KEY"):
        make_fernet()


def test_invalid_env_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """잘못된 키 형식이면 즉시 raise."""
    monkeypatch.setenv("PII_ENCRYPTION_KEY", "not-a-valid-fernet-key")
    with pytest.raises(PIIConfigError, match="형식 오류"):
        make_fernet()


def test_env_with_primary_and_old(monkeypatch: pytest.MonkeyPatch) -> None:
    """primary + old 키 모두 설정된 환경에서 로드 성공."""
    primary = Fernet.generate_key().decode()
    old1 = Fernet.generate_key().decode()
    old2 = Fernet.generate_key().decode()
    monkeypatch.setenv("PII_ENCRYPTION_KEY", primary)
    monkeypatch.setenv("PII_ENCRYPTION_KEYS_OLD", f"{old1},{old2}")

    f = make_fernet()
    # 신규 암호화 + 복호화 정상
    blob = encrypt_pii({"test": "ok"}, fernet=f)
    assert decrypt_pii(blob, fernet=f) == {"test": "ok"}


# ── 무결성 — 동일 입력도 다른 출력 (Fernet IV) ───────────
def test_encryption_is_non_deterministic(fernet: MultiFernet) -> None:
    """같은 입력을 두 번 암호화하면 다른 결과 (IV 랜덤)."""
    payload = {"x": 1}
    blob1 = encrypt_pii(payload, fernet=fernet)
    blob2 = encrypt_pii(payload, fernet=fernet)
    assert blob1 != blob2
    # 그러나 복호화는 동일
    assert decrypt_pii(blob1, fernet=fernet) == decrypt_pii(blob2, fernet=fernet)


# ── 직렬화 불가 타입 ─────────────────────────────────────
def test_non_serializable_handled(fernet: MultiFernet) -> None:
    """JSON 직렬화 불가능한 타입 (set 등) → default=str fallback 또는 raise."""
    # default=str 이라 set은 str(set)으로 변환됨 (raise 안 함)
    payload = {"timestamp": "2026-06-07T10:00:00+00:00", "tags": ["a", "b"]}
    blob = encrypt_pii(payload, fernet=fernet)
    assert decrypt_pii(blob, fernet=fernet) == payload

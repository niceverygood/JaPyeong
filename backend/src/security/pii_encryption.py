"""PII 컬럼 암호화 — birth_record.encrypted_payload 등 민감정보 보호.

설계 (개인정보보호법 준수):
  - 알고리즘: Fernet (AES-128-CBC + HMAC-SHA256, 인증 암호화)
  - 다중 키: MultiFernet — 키 로테이션 무중단
  - 버전 prefix (1 byte): 미래 envelope encryption (KMS) 마이그레이션 대비
  - JSON 직렬화: dict ↔ bytes 일관 처리
  - 환경변수 미설정 시 raise (운영 환경에서만 사용)
  - 테스트는 별도 키 주입으로 verify

환경변수:
  PII_ENCRYPTION_KEY        — 현재 primary key (base64 32 bytes Fernet key)
  PII_ENCRYPTION_KEYS_OLD   — comma-separated 이전 키들 (로테이션 grace)

키 생성:
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

로테이션 절차:
  1. 새 키 생성 → PII_ENCRYPTION_KEY 로 설정, 이전 키는 PII_ENCRYPTION_KEYS_OLD 로
  2. 신규 암호화는 새 키 사용 / 기존 데이터는 이전 키로 복호화 가능
  3. 백그라운드 작업으로 기존 데이터 재암호화 (선택)
  4. 모든 데이터 재암호화 완료 후 PII_ENCRYPTION_KEYS_OLD 제거

성능 (참고):
  - Fernet 암호화: ~5μs (작은 payload)
  - JSON 직렬화: ~20μs
  - 1초당 ~40,000 회 (단일 코어)
"""

from __future__ import annotations

import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

# 버전 prefix — 1 byte로 알고리즘 식별
# 0x01 = Fernet (AES-128-CBC + HMAC-SHA256)
# 0x02 = (예약, 미래 envelope encryption)
VERSION_FERNET = 0x01


class PIIEncryptionError(Exception):
    """암호화 / 복호화 실패."""


class PIIConfigError(Exception):
    """키 설정 오류 (환경변수 누락 / 형식 오류)."""


def _load_keys_from_env() -> list[bytes]:
    """환경변수에서 키 로드. 첫 번째 = primary (암호화), 나머지 = fallback (복호화)."""
    primary = os.environ.get("PII_ENCRYPTION_KEY", "").strip()
    if not primary:
        raise PIIConfigError(
            "PII_ENCRYPTION_KEY 환경변수 미설정. "
            "키 생성: python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"",
        )

    keys = [primary.encode()]
    old_str = os.environ.get("PII_ENCRYPTION_KEYS_OLD", "").strip()
    if old_str:
        keys.extend(k.strip().encode() for k in old_str.split(",") if k.strip())

    # 유효성 검증 — 잘못된 키면 즉시 raise
    for k in keys:
        try:
            Fernet(k)
        except (ValueError, TypeError) as e:
            raise PIIConfigError(f"Fernet 키 형식 오류: {e}") from e
    return keys


def make_fernet(keys: list[bytes] | None = None) -> MultiFernet:
    """MultiFernet 인스턴스 생성. 테스트 시 keys 인자로 키 주입.

    프로덕션에서는 keys=None → 환경변수 자동 로드.
    """
    if keys is None:
        keys = _load_keys_from_env()
    if not keys:
        raise PIIConfigError("키가 최소 1개 필요합니다.")
    return MultiFernet([Fernet(k) for k in keys])


def encrypt_pii(payload: dict[str, Any], fernet: MultiFernet | None = None) -> bytes:
    """dict payload → 암호화된 bytes (버전 prefix 포함).

    Args:
        payload: JSON-serializable dict
        fernet: 테스트 주입용 (None 이면 환경변수 기반)

    Returns:
        bytes (1 byte version + Fernet token)
    """
    if fernet is None:
        fernet = make_fernet()
    try:
        plaintext = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise PIIEncryptionError(f"JSON 직렬화 실패: {e}") from e
    token = fernet.encrypt(plaintext)
    return bytes([VERSION_FERNET]) + token


def decrypt_pii(blob: bytes, fernet: MultiFernet | None = None) -> dict[str, Any]:
    """암호화된 bytes → dict payload.

    Args:
        blob: encrypt_pii() 결과 bytes
        fernet: 테스트 주입용 (None 이면 환경변수 기반)

    Raises:
        PIIEncryptionError: 키 불일치 / 변조 / 형식 오류
    """
    if not blob:
        raise PIIEncryptionError("빈 blob")
    if len(blob) < 2:
        raise PIIEncryptionError("blob이 너무 짧음 (version + token)")

    version = blob[0]
    token = blob[1:]

    if version != VERSION_FERNET:
        raise PIIEncryptionError(
            f"지원하지 않는 암호화 버전: {version:#x}. "
            "데이터가 미래 버전 또는 손상되었을 가능성.",
        )

    if fernet is None:
        fernet = make_fernet()
    try:
        plaintext = fernet.decrypt(token)
    except InvalidToken as e:
        raise PIIEncryptionError(
            "복호화 실패 — 키 불일치 또는 데이터 변조 (Fernet InvalidToken). "
            "PII_ENCRYPTION_KEYS_OLD 에 이전 키 추가 필요할 수 있음.",
        ) from e

    try:
        return json.loads(plaintext.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise PIIEncryptionError(f"JSON 역직렬화 실패: {e}") from e


def rotate(old_blob: bytes, fernet: MultiFernet | None = None) -> bytes:
    """기존 token을 현재 primary 키로 재암호화 (rotation 마이그레이션용).

    데이터를 복호화하지 않고도 새 키로 재서명 — 운영 부하 최소화.
    """
    if not old_blob or len(old_blob) < 2:
        raise PIIEncryptionError("blob이 너무 짧음")
    if old_blob[0] != VERSION_FERNET:
        raise PIIEncryptionError(f"미지원 버전: {old_blob[0]:#x}")
    if fernet is None:
        fernet = make_fernet()
    try:
        new_token = fernet.rotate(old_blob[1:])
    except InvalidToken as e:
        raise PIIEncryptionError(f"rotation 실패 — 키 불일치: {e}") from e
    return bytes([VERSION_FERNET]) + new_token


def is_encrypted(blob: bytes) -> bool:
    """blob이 PII encryption format인지 확인 (마이그레이션 보조)."""
    return bool(blob) and len(blob) >= 2 and blob[0] in (VERSION_FERNET,)


def generate_key() -> str:
    """새 Fernet 키 생성 (운영자 키 발급용)."""
    return Fernet.generate_key().decode()

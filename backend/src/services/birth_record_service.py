"""birth_record 암호화·복호화 헬퍼 — PII 보호 + 사주 엔진 입력 변환.

사용 흐름:
  [신규 가입] BirthInfo (pydantic) → encrypt_birth() → bytes → DB 저장
  [조회·일진] DB bytes → decrypt_birth() → BirthInfo → build_pillars() → FourPillars

PII는 logs/exceptions에 남기지 않음. 평문 dict는 메모리 외 노출 금지.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.pillars import build_pillars
from src.engine.schema import BirthInfo, FourPillars
from src.security.pii_encryption import (
    PIIEncryptionError,
    decrypt_pii,
    encrypt_pii,
)

if TYPE_CHECKING:
    from cryptography.fernet import MultiFernet


def encrypt_birth(birth: BirthInfo, fernet: MultiFernet | None = None) -> bytes:
    """BirthInfo → 암호화된 bytes (DB.birth_record.encrypted_payload 저장용).

    name/birth_place 같은 PII 포함. 평문 JSON 절대 저장 금지.
    """
    payload = birth.model_dump(exclude_none=False)
    return encrypt_pii(payload, fernet=fernet)


def decrypt_birth(
    encrypted_payload: bytes,
    fernet: MultiFernet | None = None,
) -> BirthInfo:
    """암호화된 bytes → BirthInfo (사주 엔진 입력으로 사용).

    Raises:
        PIIEncryptionError: 복호화 실패 / 변조 / 키 불일치
        ValueError: 복호화 성공했으나 BirthInfo 스키마 위반
    """
    payload = decrypt_pii(encrypted_payload, fernet=fernet)
    # pydantic 이 잘못된 필드 시 ValidationError raise → 호출자가 처리
    return BirthInfo(**payload)


def decrypt_birth_to_pillars(
    encrypted_payload: bytes,
    fernet: MultiFernet | None = None,
) -> FourPillars:
    """end-to-end 헬퍼: bytes → BirthInfo → FourPillars.

    cron / 자문위원 매칭 / 일진 계산 등에서 한 줄로 사용.
    실패 시 PIIEncryptionError 또는 pydantic ValidationError.
    """
    birth = decrypt_birth(encrypted_payload, fernet=fernet)
    return build_pillars(birth)


def safe_decrypt_to_pillars(
    encrypted_payload: bytes,
    fernet: MultiFernet | None = None,
) -> FourPillars | None:
    """예외 swallow 버전 — cron 처럼 한 건 실패가 전체 작업을 막아선 안 될 때.

    실패 사유는 caller가 별도 로깅 (이 함수는 PII가 남는 로그 만들지 않음).
    """
    try:
        return decrypt_birth_to_pillars(encrypted_payload, fernet=fernet)
    except (PIIEncryptionError, ValueError, TypeError):
        return None

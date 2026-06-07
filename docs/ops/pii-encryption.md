# 자평 PII 암호화 운영 가이드

> **목적**: 사용자 출생정보 (PII) 컬럼 암호화 → 개인정보보호법 준수 + DB 유출 시 평문 노출 차단
> **알고리즘**: Fernet (AES-128-CBC + HMAC-SHA256, 인증 암호화)
> **키 관리**: MultiFernet 다중 키 — 무중단 로테이션 지원

---

## 1. 첫 설정 — 키 생성·배포

### 1.1 키 생성
```bash
# backend 디렉터리에서
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

출력 예시:
```
gAAAAABl7XQpL...44자 base64 문자열
```

### 1.2 환경변수 등록

**Vercel** (Production / Preview / Development 각각):
```
PII_ENCRYPTION_KEY=gAAAAABl7XQpL...
```

**로컬 개발** (.env):
```
PII_ENCRYPTION_KEY=gAAAAABl7XQpL...
```

⚠ **절대 git 에 커밋 금지**. .gitignore 확인.

### 1.3 검증
```bash
PII_ENCRYPTION_KEY="..." python -c "
from src.security.pii_encryption import encrypt_pii, decrypt_pii
b = encrypt_pii({'test': 'ok'})
print('roundtrip:', decrypt_pii(b))
"
```

---

## 2. 키 로테이션 — 무중단 절차

### 2.1 새 키 생성
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2.2 환경변수 업데이트 (Vercel)
```
PII_ENCRYPTION_KEY=새_키
PII_ENCRYPTION_KEYS_OLD=이전_키
```

→ 이제 신규 암호화는 새 키, 기존 데이터는 이전 키로 복호화 가능.

### 2.3 (선택) 백그라운드 재암호화
```python
# scripts/rotate_pii_keys.py 예시
from sqlalchemy import select
from src.core.db import _session_factory
from src.models.db_models import BirthRecord
from src.security.pii_encryption import rotate

async with _session_factory()() as s:
    rows = (await s.execute(select(BirthRecord))).scalars().all()
    for r in rows:
        r.encrypted_payload = rotate(r.encrypted_payload)
    await s.commit()
```

### 2.4 이전 키 제거
백그라운드 재암호화 완료 후 (또는 모든 데이터가 새 키로 갱신됐다고 확신할 때):
```
PII_ENCRYPTION_KEYS_OLD=  (제거)
```

---

## 3. 운영 시나리오

### 3.1 일진 cron 이 사용자 사주 복호화 실패 시
- `safe_decrypt_to_pillars()` 가 None 반환 → 해당 사용자만 스킵
- 다른 사용자에 영향 없음
- 운영자 점검: notification_log 의 status 검토 + 해당 user_id 확인

### 3.2 DB 유출 시
- DB 덤프만으로는 평문 PII 복호화 불가 (인증 암호화)
- 단, `PII_ENCRYPTION_KEY` 환경변수도 함께 유출되면 평문 복호화 가능
  → 환경변수와 DB는 다른 보안 경계에서 보관 (Vercel + DB provider 분리)

### 3.3 키 분실 시
- 평문 복원 불가 (의도된 보안)
- 영향: 사용자가 사주 재입력 필요
- 예방: 키 백업 (1Password 등 비밀번호 관리자 또는 KMS 도입 검토)

---

## 4. 미래 마이그레이션 — Envelope Encryption (KMS)

현재 `VERSION_FERNET = 0x01` prefix 가 모든 blob에 들어가 있어,
미래 KMS (AWS KMS, GCP KMS, Vault Transit) 도입 시:
- `VERSION_KMS_V1 = 0x02` 신규 정의
- 신규 암호화는 KMS, 기존 Fernet (0x01) 데이터는 복호화 fallback
- 점진적 마이그레이션 가능

---

## 5. 컴플라이언스 체크리스트

| 항목 | 상태 | 비고 |
|---|---|---|
| 개인정보보호법 — 암호화 의무 (생년월일 등 식별 가능 정보) | ✅ Fernet AES-128 | |
| ISMS-P — 키 관리 정책 문서화 | ⏳ 본 문서 |  |
| 키 분리 (코드 ≠ 환경변수 ≠ DB) | ✅ |  |
| 키 로테이션 절차 명문화 | ✅ |  |
| 무결성 검증 (HMAC) | ✅ Fernet 내장 |  |
| 14세+ 자녀 동의 게이트 | ✅ (BM v2 model `family_member`) |  |
| 30일 이내 파기 절차 | ⏳ Sprint 1-2 회원 탈퇴 구현 시 |  |

---

## 6. 비상 대응

### 6.1 평문 PII가 로그에 노출됨
1. 즉시 해당 로그 영구 삭제 (Vercel logs API)
2. 노출 범위 조사 (CloudFront / Vercel logs / Datadog 모두)
3. 영향받은 사용자 식별 → 개인정보위 신고 (영향 사용자 1,000명+ 시 의무)
4. 로그 마스킹 코드 점검: `logger.info("user=%s", user_id)` ✅ / `logger.info("birth=%s", birth_dict)` ❌

### 6.2 키 유출 의심 시
1. 즉시 새 키 생성 + 환경변수 교체 (운영 페이지 잠금 X — 무중단)
2. 백그라운드 재암호화 즉시 가동
3. 24시간 내 모든 데이터 재암호화 → 이전 키 폐기
4. 사용자 통보 의무 검토 (KISA 가이드)

---

**작성**: 2026-06-07 · 자평 운영팀
**다음 갱신**: 첫 키 발급 + 운영 적용 후

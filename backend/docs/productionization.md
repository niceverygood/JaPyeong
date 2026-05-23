# 자평 상용화 핸드오프 (2026-05-23)

이 세션에서 끝낸 것과 **남은 작업·필요 자격증명**을 한 곳에 정리합니다.
운영 환경(`ja-pyeong.vercel.app`)에서 곧바로 살아나는 항목과, 사용자가 시크릿/계정을 넣어야 살아나는 항목을 분리해 두었습니다.

---

## ✅ 이번 세션에서 완료한 상용화 작업

### AI 자문 채팅 (핵심 제품)
- **백엔드** `POST /api/v1/chat` (`backend/src/ai/`, `backend/src/api/v1/chat.py`)
  - 3층 책임 분리: 룰베이스 `saju_service.analyze_natal` → Claude(`anthropic` SDK) → 후처리 가드레일
  - 시스템 프롬프트는 CLAUDE.md 사양(자문 톤·단정 금지·근거 표기·자살 키워드 처리)을 그대로 반영
  - 모델: `claude-sonnet-4-5` (env `ANTHROPIC_MODEL_STANDARD`로 오버라이드)
- **가드레일** (`backend/src/ai/guardrails.py`)
  - 입력 위기 키워드(자살·자해) → 즉시 상담 자원 안내로 답을 대체
  - 출력에서 단정형(`반드시 ~`, `무조건 ~`) 패턴 + 의학·법률 단정 키워드 검출 → 보강/플래그
- **모바일 UI** (`mobile/src/screens/Chat/ChatScreen.tsx`)
  - 추천 칩 5종(진로/관계/재정/건강/결단), 사용자 말풍선 + 자문 카드(근거 + 인용 + 후속 질문 칩)
  - 원국 화면에 "AI 자문 시작하기 →" 버튼 추가

### 사전예약 실수집
- `POST /api/preorder` (`api/index.py`)
  - 이메일 검증, **Vercel 함수 로그에 구조화 JSON 기록**(항상)
  - `PREORDER_WEBHOOK_URL` 환경변수 설정 시 동일 페이로드 외부 웹훅 전송(실패해도 사용자 응답 200)
- 랜딩 페이지 모달 — `fetch('/api/preorder')`로 실제 전송, "데모 환경" 안내 제거, 실패 시 인라인 에러 표시

### 폴리시 페이지 (DRAFT)
- `web/privacy.html` — 개인정보처리방침 (10조, "DRAFT · 법무 검토 필요" 라벨)
- `web/terms.html` — 이용약관 (9조 + 책임 한계 박스)
- 랜딩 푸터에 두 페이지 링크 추가

---

## 🟡 자격증명만 넣으면 즉시 동작하는 것

### 1. AI 자문 채팅 — Anthropic API 키
**필요**: Vercel 프로젝트 환경변수에 `ANTHROPIC_API_KEY` 추가 (Production 스코프).

```
ANTHROPIC_API_KEY=sk-ant-...
# 선택: 모델 오버라이드
ANTHROPIC_MODEL_STANDARD=claude-sonnet-4-5
```

키가 없을 때 동작: `/api/v1/chat` 호출 시 **503 + "ANTHROPIC_API_KEY 미설정"** 응답. 프론트는 에러 카드 표시.

### 2. 사전예약 외부 수집 — 웹훅 URL (선택)
Vercel 로그만으로도 데이터는 100% 보존되지만, 실시간 알림/시트 적재가 필요하면:

```
PREORDER_WEBHOOK_URL=https://hooks.slack.com/...  # 또는 Google Apps Script, Make.com
```

페이로드: `{ type, email, name, plan, source, at }`.

---

## 🔴 사용자 의사결정 + 자격증명이 필요한 다음 단계

### A. 회원·DB·대화 영구 저장
지금은 출생정보가 Zustand(브라우저 메모리)에만 있고, 대화는 화면 단위로 휘발됩니다. 영구화에는 다음이 필요:

| 항목 | 추천 | 대안 |
|---|---|---|
| Postgres 호스팅 | **Supabase** (DB+Auth+Storage 통합, 무료 티어 충분) | Neon, Railway Postgres, AWS RDS |
| 인증 | Supabase Auth (Kakao/Google OIDC) | Clerk, NextAuth, Auth0 |
| 마이그레이션 | Alembic (이미 디렉토리 존재: `backend/alembic/`) | Supabase migrations |

**필요한 결정**: 위 스택 선택 → 회원가입 후 URL/anon key 제공.
**필요한 스키마** (제가 다음 세션에 작성 가능):
- `users` (id, email, kakao_id?, created_at)
- `birth_records` (id, user_id, gender, calendar, ymdhm, longitude, latitude, encrypted_payload)
- `conversations` (id, user_id, birth_id, created_at)
- `messages` (id, conversation_id, role, content, basis, citations_json, created_at)
- `preorders` (id, email, name, plan, source, created_at) — 현재 로그→DB로 승격
- `subscriptions` (id, user_id, plan, portone_subscription_id, status, started_at, expires_at)

### B. 결제·구독
| 항목 | 필요 |
|---|---|
| PortOne V2 가맹점 | `PORTONE_API_SECRET`, `PORTONE_STORE_ID` |
| 카카오페이 정기결제 | `KAKAO_CID` (이미 `CT97630018` 보유), `KAKAO_ADMIN_KEY` |
| 웹훅 엔드포인트 | `/api/webhooks/portone`, `/api/webhooks/kakao` (서명 검증) |

**구현 범위 (확정 시)**: 결제 시작 → 콜백 → `subscriptions` 행 갱신 → `/api/me/subscription` 조회 → 모바일 결제 화면. Pro 단건은 일회성 인텐트.

### C. 🔴 명리 정통성 (격국·용신·자문위원 검증)
가장 큰 미충족 게이트. 코드만으로 못 푸는 영역:
- **검증 케이스 0건** — 출시 게이트(`RUN_GATE_CHECK=1`) 100건 미달
- **`strength`/`geokguk`/`yongsin` 미작성** — `myeongri-policy.md` 항목 7·8 자문위원 확정 필요
- 권장: 자문위원 1명 이상 영입 → 표준 검증 케이스 30건 수집부터 시작 → 모듈 착수

### D. 운영 인프라
| 항목 | 메모 |
|---|---|
| 도메인 | 현재 `ja-pyeong.vercel.app` (서브). 정식 도메인(예: `japyeong.kr`) 연결 시 SEO·이메일 도메인 통일 |
| 모니터링 | Sentry (`SENTRY_DSN`) — 백엔드/모바일 |
| 로그 보존 | Vercel 로그는 단기. 장기 보존 필요 시 Logflare/Axiom 등 |
| 출생정보 암호화 | `PII_ENCRYPTION_KEY` (`.env.example`에 자리 있음). DB 도입 시 컬럼 암호화에 사용 |
| 법무 | privacy/terms.html은 **DRAFT** — 변호사 검토 후 발효. 회사명·사업자번호·주소 자리에 placeholder 사용 중 |

---

## 환경변수 체크리스트 (Vercel)

```
# === 필수(AI 자문 활성화) ===
ANTHROPIC_API_KEY=sk-ant-...

# === 선택(사전예약 외부 적재) ===
PREORDER_WEBHOOK_URL=https://...

# === 다음 단계(DB·결제 도입 시) ===
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://....supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
JWT_SECRET=...
PII_ENCRYPTION_KEY=...
PORTONE_API_SECRET=...
PORTONE_STORE_ID=...
KAKAO_ADMIN_KEY=...
SENTRY_DSN=...
```

---

## 출시 차단(blocking) 요약

| 우선 | 항목 | 누가 해결 |
|---|---|---|
| **P0** | `ANTHROPIC_API_KEY` Vercel env 설정 | 사용자 (1분) |
| **P0** | 자문위원 영입 → 검증 케이스 30건+ | 사용자 + 명리 자문위원 |
| **P1** | 회원·DB(추천: Supabase) | 사용자 계정 생성 → 코딩 (저) |
| **P1** | 결제 가맹점 자격증명 → 결제 흐름 구현 | 사용자 + PortOne 가입 |
| **P1** | 격국·용신 모듈 (`strength`→`geokguk`→`yongsin`) | 자문위원 정책 확정 + 코딩 |
| **P2** | 법무 검토(privacy/terms) | 변호사 |
| **P2** | 도메인·SEO·모니터링 | 사용자 (도메인) + 코딩 |
| **P2** | 모바일 앱스토어/플레이스토어 | 사용자 (개발자 계정) |

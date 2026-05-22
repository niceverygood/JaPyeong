# 자평 (子平 · JAPYEONG)

송나라 명리학자 서자평의 정신을 잇는 **명리학 AI 자문 SaaS**.
기존 운세 앱과 달리, 명리 정통성을 유지하면서 **룰베이스 엔진 + RAG + LLM**을 결합해
의사결정 자문을 제공합니다.

> 풀이는 100% AI지만, LLM이 사주를 직접 계산하지 않습니다.
> **룰베이스 엔진이 사주 구조를 확정 → LLM이 해석·자문**하는 3층 아키텍처가 핵심입니다.

---

## 아키텍처 (3층)

```
사용자 입력
   │
   ▼
[Layer 1] 룰베이스 엔진 (Python, 결정론적)
   진태양시·절기·60갑자·격국·용신·신강신약·대운·세운 → structured JSON
   │
   ▼
[Layer 2] LLM (Claude, 자문 생성)
   룰베이스 JSON + 사용자 질문 + RAG 패시지 → 자연어 자문
   │
   ▼
[Layer 3] 후처리 가드레일
   단정·의학/법률 단정 차단, 자살/자해 키워드 → 상담 안내
```

**원칙**: 사주 계산은 절대 LLM에 위임하지 않는다(환각 위험). LLM은 통역기 역할만 한다.

---

## 기술 스택

| 영역 | 스택 |
|---|---|
| 백엔드 | Python 3.11+, FastAPI, SQLAlchemy(async), Alembic |
| DB / 캐시 | PostgreSQL 16 + pgvector, Redis 7 |
| LLM | Anthropic API (Sonnet 4.6 표준 / Haiku 4.5 일진 / Opus 4.7 심층) |
| 임베딩 | voyage-multilingual-2 |
| 결제 | PortOne V2, 카카오페이 정기결제 |
| 모바일 | React Native (Expo SDK 51+ managed), Zustand, TanStack Query, NativeWind |

---

## 디렉토리 구조

```
japyeong/
├── backend/          # FastAPI + 명리 엔진 (가장 중요)
│   ├── src/engine/   # ★ 룰베이스 명리 엔진
│   ├── src/rag/      # 고전 RAG 파이프라인
│   ├── src/ai/       # LLM 자문 + 가드레일
│   ├── src/api/      # REST 엔드포인트
│   └── tests/engine/ # 명리 엔진 회귀 테스트 (검증 케이스 100건+)
├── mobile/           # React Native (Expo) 앱
│   └── src/theme/    # 자평 디자인 시스템
└── assets/design/    # UX/UI 참고 (mobile-screens.html)
```

---

## 로컬 개발 시작하기

### 1. 인프라 (Postgres + Redis)
```bash
cp .env.example .env        # 값 채우기
docker compose up -d
```

### 2. 백엔드
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.main:app --reload     # http://localhost:8000/docs
pytest                            # 엔진 회귀 테스트
```

### 3. 모바일
```bash
cd mobile
npm install
npx expo start
```

---

## 개발 로드맵

| Phase | 내용 | 상태 |
|---|---|---|
| 0 | 셋업 (구조·설정·docker) | ✅ 진행 중 |
| 1 | **명리 엔진** (검증 케이스 100건 + TDD) | ⬜ |
| 2 | API 골격 (auth/users/saju) | ⬜ |
| 3 | RAG 파이프라인 (고전 6종) | ⬜ |
| 4 | AI 자문 (프롬프트·라우팅·가드레일) | ⬜ |
| 5 | 결제·구독 | ⬜ |
| 6 | 모바일 앱 | ⬜ |
| 7 | 베타 (50명) | ⬜ |
| 8 | 정식 출시 | ⬜ |

상세 가이드·코딩 컨벤션·명리 도메인 용어는 [`CLAUDE.md`](CLAUDE.md) 참고.

---

## 핵심 개발 원칙

1. **명리 엔진은 TDD 필수** — 검증 케이스 없이 코드 작성 금지.
2. **사주 8자 추출은 100% 일치** — 진태양시·절기 보정 누락 시 사주 전체 무효.
3. **LLM은 단정 금지** — "~로 봅니다" 자문 톤, 모든 답변에 명리 근거·출처 표기.
4. **PII 보호** — 출생정보 평문 로그 금지, 암호화 저장. 카드정보는 PortOne 토큰만 보관.
5. **저작권** — 명리 고전(저작권 만료)만 임베딩, 현대 명리서 무단 사용 금지.

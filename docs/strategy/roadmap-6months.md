# 자평 6개월 실행 로드맵 (26주, 12 스프린트)

> 출처: BM v2 마스터 설계 + 3중 적대적 검증
> 단위: 2주 = 1 스프린트
> 원칙: **Sprint 1-6에 보험 4종(자녀 보류 / 톤다운 / rate limit / 자문위원 5명)** 모두 박기

---

## Sprint 1-2 (Week 1-4) — 결제·회원·DB·기본 paywall

**목표**: 돈 받을 수 있는 상태 만들기 + 정체성 가드레일 인프라

| # | 작업 | 파일/모듈 | DoD |
|---|---|---|---|
| 1 | 회원 DB 스키마 | `prisma/schema.prisma` 또는 `db/migrations/001_init.sql` (users, subscriptions, payments, decision_logs) | 마이그레이션 성공 |
| 2 | 토스/카카오페이 결제 연동 | `backend/src/payment/toss.ts`, `kakao.ts` | 테스트 결제 1건 성공 |
| 3 | 기본 paywall 컴포넌트 | `mobile/src/components/Paywall.tsx` | 무료/유료 분기 작동 |
| 4 | 디스클레이머 글로벌 컴포넌트 | `mobile/src/components/LegalDisclaimer.tsx` | 결과지 상단 고정 노출 |
| 5 | **금지어 사전 + CI 훅** | `scripts/forbidden-words.txt` + `.github/workflows/copy-lint.yml` | PR에서 금지어 시 자동 fail |
| 6 | 약관·개인정보처리방침 v2 | `web/terms.html`, `web/privacy.html` | 법무 검토 |
| 7 | **rate limit 다층 방어** | `backend/src/middleware/rate-limit.ts` (회원·일·IP·디바이스) | 디시 폭주 시뮬 테스트 통과 |
| 8 | **Anthropic budget alert** | infra script + Slack webhook | 일 100만원 임계 알림 |

---

## Sprint 3-4 (Week 5-8) — 첫 hook 5개 + 일진 알림

| # | 작업 | 파일/모듈 | DoD |
|---|---|---|---|
| 9 | 무료 첫 리포트 생성 | `backend/src/report/free_report.py` | 가입→리포트 30초 내 |
| 10 | 일진 알림 cron + 푸시 | `backend/src/jobs/daily_fortune.py`, FCM 연동 | D+3부터 자동 발송 |
| 11 | 알림 빈도 조절·끄기 UI | `mobile/src/screens/Settings/Notifications.tsx` | 토글 작동 |
| 12 | 월간 흐름 미리보기 + paywall | `backend/src/report/monthly_preview.py` | 무료 3줄 → 상세 결제 |
| 13 | 결정 도우미 입력 폼 (이미 라이브) | `mobile/src/screens/Decision/DecisionScreen.tsx` | 결정 입력→결과 분리 저장 |
| 14 | 궁합 친구 데이터 동의 게이트 | `mobile/src/components/ThirdPartyConsent.tsx` | "본인 동의 받음" 체크 필수 |
| 15 | **단정 표현 자동 톤다운 후처리** | `backend/src/ai/post_process.py` | "할 것" → "할 가능성" 자동 변환 |

---

## Sprint 5-6 (Week 9-12) — 자문위원 베타 + Premium 상품

| # | 작업 | 파일/모듈 | DoD |
|---|---|---|---|
| 16 | **자문위원 영입 BD** (단위경제 #2 — 10명 컨택) | `docs/biz/advisor-pipeline.md` | 영입 5명 확정 |
| 17 | **자문위원 계약서 v1** (3년 독점 + 위약금 + 지분 옵션) | `docs/legal/advisor-contract-template.docx` | 5건 서명 |
| 18 | 자문위원 매칭 시스템 | `backend/src/advisor/match.py` + 캘린더 연동 | 예약→매칭 5분 내 |
| 19 | **녹취 동의 자동 안내 모듈** | `backend/src/voice/consent.py` | 통화 시작 시 자동 |
| 20 | Premium 상품 페이지 | `mobile/src/screens/Pricing/Premium.tsx` | 결제 가능 |
| 21 | 자문 후 결정 follow-up | `backend/src/jobs/decision_followup.py` | 3개월 후 자동 발송 |
| 22 | **PI(전문가배상책임) 보험 가입 검토** | 보험사 견적 3곳 | 견적 받음 |

---

## Sprint 7-8 (Week 13-16) — Family 패키지 + 추천·바이럴

| # | 작업 | 파일/모듈 | DoD |
|---|---|---|---|
| 23 | Family 패키지 SKU + 결제 | `mobile/src/screens/Pricing/Family.tsx`, `backend/src/payment/family_sku.py` | **자문 회차 = 1패키지당 2회 (가족 수 무관)** |
| 24 | 가족 입력 게이트 (14세 게이트) | `mobile/src/components/FamilyInputGate.tsx` | 미성년 14세+ 동의 링크 발송 |
| 25 | 친구 초대 → 궁합 무료 1회 | `backend/src/referral/sync_invite.py` | invite code 추적 |
| 26 | TM 채널 어트리뷰션 | `backend/src/attribution/tm_tag.py` | TM 코드 결제 자동 태깅 |
| 27 | **TM vs Self-serve SKU 가드** | `backend/src/payment/sku_guard.py` | TM 코드 없이 Family 결제 차단 |

---

## Sprint 9-10 (Week 17-20) — 시즌 캠페인 + B2B 베타

> ⚠ **자녀 사주 출시 보류** (윤리 검증 반영, 9개월 후 재검토)

| # | 작업 | 파일/모듈 | DoD |
|---|---|---|---|
| 28 | 신년/연말 시즌 캠페인 페이지 | `web/seasonal/year-end.html` | 시즌 트리거 자동 |
| 29 | 시즌 가격 +20% (수요 분산) | `backend/src/pricing/seasonal.py` | 시즌 자동 가격 변경 |
| 30 | 시즌 자문위원 사전 예약 (2주 전 오픈) | `backend/src/advisor/seasonal_slots.py` | 매칭 실패율 5% 이하 |
| 31 | **B2B 임원 코칭 베타** (3사 시범) | `docs/biz/b2b-pilot.md` | 1건 계약 체결 |
| 32 | B2B 전용 리포트 템플릿 | `backend/src/report/b2b_template.py` | 사례 3건 출력 |

---

## Sprint 11-12 (Week 21-26) — 갱신 시스템 + LTV 분석 + 다음 6개월 설계

| # | 작업 | 파일/모듈 | DoD |
|---|---|---|---|
| 33 | **자동갱신 opt-in 시스템 (디폴트 OFF)** | `backend/src/subscription/renewal.py` | 갱신 30/7/1일 전 3회 알림 |
| 34 | **1depth 해지 버튼** | `mobile/src/screens/Mypage/Cancel.tsx` | 클릭 2회 내 해지 |
| 35 | 코호트 리텐션 대시보드 | `backend/src/analytics/cohort.py` + Metabase | D30/D90 자동 집계 |
| 36 | 결정 만족도 follow-up 집계 | `backend/src/analytics/decision_satisfaction.py` | 6개월 결정 결과 분석 |
| 37 | **데이터 자산화 v1** (결정→결과 매핑) | `backend/src/dataset/decision_outcomes.py` | 1만건 익명 데이터셋 |
| 38 | LTV/CAC 채널별 분석 | `docs/analytics/ltv-cac-report.md` | 월간 자동 갱신 |
| 39 | **6개월 회고 + 다음 6개월 설계** | `docs/strategy/h2-2026.md` | 대표 컨펌 |

---

## 미션 크리티컬 경로 (보험 4종)

다음 4개가 **Sprint 1-6 안에 모두** 박혀야 출시 첫 분기 생존:

| 보험 | 스프린트 | 산출물 |
|---|---|---|
| ❶ 자녀 상품 보류 결정 | Sprint 1 (의사결정) | 9~12 스프린트에서 출시 배제 명문화 |
| ❷ 단정 표현 자동 톤다운 파이프라인 | Sprint 3-4 | `backend/src/ai/post_process.py` |
| ❸ rate limit 다층 방어 | Sprint 1-2 | `backend/src/middleware/rate-limit.ts` |
| ❹ 자문위원 3년 독점 5건 | Sprint 5-6 | 계약서 5건 서명 |

---

## 다음 행동 (오늘 / 이번 주)

| 시점 | 액션 | 책임 |
|---|---|---|
| 오늘 | 대표 [D-1~5] 의사결정 컨펌 | 대표 |
| 내일 | 자문위원 BD 1인 채용 공고 또는 외주 계약 | HR/대표 |
| 이번 주 | `docs/strategy/product-bm-v2.md` + `roadmap-6months.md` 초안 commit ✅ | 기획 |
| 이번 주 | `scripts/forbidden-words.txt` + CI 훅 적용 | 개발 |
| 다음 주 | Sprint 1 킥오프 (결제·DB·paywall·rate limit·디스클레이머) | 개발 전원 |
| 2주 후 | 자문위원 10명 컨택 응답 결과 보고 | BD |
| 4주 후 | 첫 유료 결제 1건 (베타) | 전원 |

---

## 대표 의사결정 5개 (Sprint 1 시작 전 컨펌 필요)

| # | 결정 | 권고 | 이유 |
|---|---|---|---|
| D-1 | **가격 변경** | ✅ 4티어 재구조 채택 | 갱신율 35~45% 가정에서도 마진 확보 |
| D-2 | **자문위원 영입 시점** | ✅ Sprint 1부터 BD 풀타임 | 영입 lead time 길어 늦으면 Sprint 5-6 베타 불가 |
| D-3 | **첫 paywall 시점** | ✅ Sprint 1-2 동시 | 무료 폭주 시 LLM 비용 자기파괴 |
| D-4 | **자녀 사주** | ✅ 6개월 보류, 9개월 후 재검토 | D-Day 시나리오 차단 |
| D-5 | **TM/Self-serve 우선순위** | ✅ 물리적 SKU 분리 병행 | 카니발리제이션·어트리뷰션 분쟁 자동 차단 |

### 추가 결정 (보너스 5개)
| D-6 | "AI 사주" → "AI 보조 고전 해석" 명칭 재정의 | ✅ |
| D-7 | 자동갱신 디폴트 OFF | ✅ |
| D-8 | 글로벌 진출 6개월 내 보류 | ✅ |
| D-9 | 빅테크 대비 — 고가·1:1·B2B 도주 | ✅ |
| D-10 | 진짜 해자 3축에 예산 30% 할당 | ✅ |

---

**작성**: 2026-06-04
**다음 갱신**: 매 스프린트 종료 시 진행률 + 다음 스프린트 조정

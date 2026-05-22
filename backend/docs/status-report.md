# 자평 백엔드 — 현재 상태 스냅샷

> "자평이 실제로 어디까지 와 있는가"의 단일 스냅샷. 점검 세션 산출물(코드 수정 없음).
> 점검 일자: 2026-05-22

## 1. 빌드/품질 게이트

| 항목 | 상태 | 비고 |
|---|---|---|
| pytest 전체 | ✅ **250 passed, 2 skipped, 0 failed** | skip 2 = 검증케이스 미수집 상태의 하네스/게이트(의도된 동작) |
| ruff (src+tests) | ✅ All checks passed | lint clean |
| 출시 게이트 `RUN_GATE_CHECK=1` | ❌ **FAIL** | 검증 케이스 **0건** / 기준 100건 (정상적으로 차단 중) |
| validation_cases 실제 파일 | **0건** | `_TEMPLATE.json`만 존재(하네스 스킵). 자문위원 승인 케이스 없음 |
| 8자 스팟체크 (5건) | ✅ **5/5 전건 일치** | `scripts/spot_check.py`, 독립 기준 대조 — 아래 §7 |

## 2. 엔진 모듈 (실제 존재 — `src/engine/`)

| 모듈 | 존재 | 역할 |
|---|---|---|
| constants.py | ✅ | 천간·지지·오행·음양·60갑자 |
| ganji.py | ✅ | 60갑자 변환·조회 |
| jijanggan.py | ✅ | 지장간(월률분야) |
| ten_gods.py | ✅ | 십성 |
| five_elements.py | ✅ | 오행 분포 |
| relations.py | ✅ | 합·충·형·해·파 (합화 미구현) |
| solar_time.py | ✅ | 진태양시 보정 |
| jeolgi.py | ✅ | 24절기 (sxtwl 래핑) |
| pillars.py | ✅ | 사주 8자 추출 ★ |
| daewoon.py | ✅ | 대운 |
| sewoon.py | ✅ | 세운·월운·일운 |
| policy.py | ✅ | 정책 플래그(12개 enum + dataclass) |
| schema.py | ✅ | Pydantic 스키마 |
| **strength.py** | ❌ 없음 | 신강신약 (🔴 자문위원 필요, 미착수) |
| **geokguk.py** | ❌ 없음 | 격국 (🔴 미착수) |
| **yongsin.py** | ❌ 없음 | 용신 (🔴 미착수) |

→ 결정론적 모듈 11/11 완료. 🔴 해석 모듈(strength/geokguk/yongsin) 3개 미착수.

## 3. API 라우트 (실제 — `src/main.py` + `src/api/`)

| 메서드 | 경로 | 핸들러 | 비고 |
|---|---|---|---|
| GET | `/` | root | `/docs`로 307 리다이렉트 |
| GET | `/health` | health | 헬스체크 |
| POST | `/v1/saju/analyze` | analyze | 원국 8자·십성·오행·관계·대운 |
| GET | `/v1/saju/luck` | luck | 세운·월운·일운(일자별) |
| GET | `/docs` `/redoc` `/openapi.json` | (FastAPI 기본) | API 문서 |

→ 실서비스 라우트 2개(analyze/luck). 인증·결제·DB·LLM 라우트 없음.

## 4. 모듈별 동작 중인 policy default

현재 `get_default_policy()` 값 (전 항목 **자문위원 미확정 = 잠정**):

| policy 항목 | default | 직접 사용 모듈 | 간접(전파) |
|---|---|---|---|
| solar_time | `with_eot` | solar_time | pillars, daewoon, sewoon |
| jasi | `unified` | (pillars 시지 산출 로직) | — |
| sesu | `ipchun` | jeolgi | pillars, sewoon, daewoon |
| wolju_boundary | `jeol` | jeolgi | pillars, sewoon |
| leap_month | `by_jeolgi` | (음력 변환 경로) | pillars |
| day_change | `midnight` | pillars | — |
| geokguk_priority | `tuchul_first` | (미사용 — geokguk 미착수) | — |
| yongsin_method | `eokbu` | (미사용 — yongsin 미착수) | — |
| sinsal_scope | `twelve_only` | (미사용) | — |
| daewoon_calc | `days_div3` | daewoon | — |
| unknown_hour | `exclude` | pillars | — |
| lunar_input | `accept` | pillars | — |
| lunar_converter | `sxtwl` | (jeolgi/pillars/sewoon가 sxtwl 직접 사용) | — |

→ **pillars는 사실상 모든 시간 관련 정책에 의존**(solar_time/jeolgi에 policy를 그대로 전달). 8자는 위 잠정 default 가정 위에 서 있음.

## 5. 외부 의존 / 미구현 지점

| 항목 | 상태 |
|---|---|
| sxtwl (만세력) | 일주·절기·음력변환에 사용. anchor 2000-01-07=甲子로 교차검증됨(§7) |
| 합화(合化) 판정 | `relations.detect_hap_hwa` → NotImplementedError (학설차) |
| 시주 추정 | `pillars` ESTIMATE 정책 → NotImplementedError |
| 월경계 중기/세수 동지 | `jeolgi` JUNGGI/DONGJI → NotImplementedError |
| 신강신약·격국·용신 | 모듈 자체 미작성 |
| AI 자문(LLM/RAG) | 미착수 (Phase 4) |
| 인증·결제·DB persistence | 미착수 |

## 6. 모바일

| 항목 | 상태 |
|---|---|
| API 연동(types/client/hooks) | ✅ tsc 통과, 번들 빌드 성공 |
| 온보딩·원국 화면 | ✅ 시뮬레이터 렌더 확인 |
| 세운 캘린더·탭·결제 화면 | ❌ 미작성 |

## 7. 8자 스팟체크 상세 (`scripts/spot_check.py`)

검증 케이스 100건 게이트와 별개의 **일회성 독립 점검**. longitude=None(진태양시 off, 시계시=기준 동일).

| 기둥 | 기준(독립성) | 결과(5건) |
|---|---|---|
| 년주 | 60갑자 공인 년주표(1984=甲子) — 독립 | 5/5 ✓ |
| 일주 | 공인 anchor 2000-01-07=甲子, 60일 순환 직접계산 — **독립** | 5/5 ✓ |
| 시주 | 五鼠遁 고전 규칙 독립 구현 — 독립 | 5/5 ✓ |
| 월주 | sxtwl getMonthGZ 교차참조 (월간 부분독립) | 5/5 ✓ |

→ **일주가 anchor 독립계산과 전건 일치** = sxtwl 기반 일주의 신뢰 근거.
→ 단, **진태양시 경로**(longitude 有, 경계 시각)와 **음력 변환**은 이 스팟체크 범위 밖
  (단위 테스트로만 커버). 경계 케이스는 검증 케이스 100건에서 별도 확인 필요.

## 8. pillars 진입(신뢰) 가능 여부 판정

phase1-roadmap.md 기준 `pillars`는 **검증 케이스 30건+ 동반이 전제**.

- **현황**: `pillars.py`는 **이미 구현 완료**(테스트 23건 통과)이나, 이를 뒷받침하는
  **자문위원 검증 케이스는 0건**.
- **판정**: **"구현됨 · 미검증(unverified)" 상태.** 스팟체크 5건(독립 기준)은 통과했으나
  로드맵 게이트(30건)·출시 게이트(100건) 모두 미충족.
- **결론**:
  - 기술적으로 동작하고 비경계 케이스는 신뢰 가능(스팟체크 근거).
  - 그러나 "검증 완료"로 표기 불가 — **검증 케이스 수집이 다음 선결 작업**.
  - 하류 🔴 모듈(strength/geokguk/yongsin)은 pillars 검증 + 정책 7·8 확정 전 착수 금지(로드맵 준수).

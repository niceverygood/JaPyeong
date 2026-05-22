# Phase 1 로드맵 — 명리 엔진 모듈 (정책 의존도 순)

> Phase 1의 남은 엔진 모듈을 **정책 의존도**(=[myeongri-policy.md](myeongri-policy.md) 확정 필요 정도) 순으로 정렬합니다.
> 의존도 낮은 모듈부터 TDD로 진행하고, 그 사이 자문위원 영입 + 정책 확정 + 검증 케이스 수집을 병행합니다.
>
> 완료: `constants.py`, `schema.py`, `ganji.py`, `policy.py`, 검증 하네스.

## 의존도 분류 표

| 모듈 | 정책 의존도 | 의존 모듈 | 검증 케이스 필요 | 예상 세션 |
|---|---|---|---|---|
| `jijanggan.py` | 🟢 낮음 | constants | 0 (룩업 자체검증) | N+1 |
| `ten_gods.py` | 🟢 낮음 | constants, ganji, schema, jijanggan | 0~5 (분포 대조용) | N+1 |
| `five_elements.py` | 🟢 낮음 | constants, ganji, jijanggan | 5 (오행 분포) | N+2 |
| `relations.py` | 🟢 낮음 | constants, ganji | 5 (합충형해파) | N+2 |
| `solar_time.py` | 🟡 중간 | policy, (astronomy) | 5 (보정 시각) | N+3 |
| `jeolgi.py` | 🟡 중간 | policy, (astronomy/lib) | 10 (절입 시각) | N+3 |
| `pillars.py` | 🟡 중간 | solar_time, jeolgi, ganji, policy | 30+ (8자 100%) | N+4 |
| `strength.py` | 🔴 높음 | pillars, jijanggan, ten_gods, five_elements, policy | 50+ | N+5 |
| `geokguk.py` | 🔴 높음 | pillars, jijanggan, ten_gods, strength, policy | 50+ | N+6 |
| `yongsin.py` | 🔴 높음 | strength, geokguk, five_elements, policy | 50+ | N+7 |
| `daewoon.py` | ⚫ 최종 | pillars, jeolgi, policy | 20 | N+8 |
| `sewoon.py` | ⚫ 최종 | pillars, daewoon, ganji, policy | 10 | N+8 |

> 검증 케이스 "필요"는 해당 모듈을 신뢰 수준으로 검증하기 위한 **최소 권장치**입니다.
> 누적 100건 출시 게이트는 별도(`RUN_GATE_CHECK=1`).

---

## 🟢 정책 의존 낮음 (즉시 가능)

### `jijanggan.py` — 지장간
- **시그니처**: `get_jijanggan(ji: str) -> list[HiddenStem]` / `get_primary_stem(ji: str) -> str`
- **policy 의존**: 없음 (지장간 배합은 명리 유파 공통 — 일수 배분은 통설 채택, 근거 docstring 표기)
- **검증 케이스**: 0 (12지지 룩업이 곧 자체검증)
- **차단 의존성(blocking)**: `ten_gods(include_hidden)`, `five_elements`, `strength` 가 이 모듈을 사용 → **선행 필수**

### `ten_gods.py` — 십성
- **시그니처**: `get_ten_god(day_master: str, other: str) -> TenGod` / `count_ten_gods_in_pillars(day_master, pillars, include_hidden=False) -> TenGodsCount`
- **policy 의존**: 없음 (음양·오행 생극 관계는 공통). 단 `include_hidden` 집계 시 지장간 정기만 — 정책 무관.
- **검증 케이스**: 0~5 (`ten_gods_count` 대조용은 pillars 완성 후)
- **차단 의존성**: `strength`, `geokguk` 가 사용 → 선행 필수

### `five_elements.py` — 오행 분포
- **시그니처**: `count_five_elements(pillars, policy, include_hidden=True) -> dict[Ohaeng, float]`
- **policy 의존**: 가중치(천간 vs 지장간 비중, 통근 가산) 일부 — **default로 진행 가능**, 정밀 가중은 자문위원 확정 권장. 정책 분기 시 중단·질의.
- **검증 케이스**: 5
- **차단 의존성**: `strength`, `yongsin` 가 사용

### `relations.py` — 합·충·형·해·파
- **시그니처**: `find_relations(pillars) -> list[Relation]` (천간합·지지육합·삼합·방합·충·형·해·파)
- **policy 의존**: 없음 (조합 규칙 공통). 단 합화(合化) 성립 조건은 학설 차 → **합/충 판정만 우선**, 합화 성립은 TODO + 자문위원.
- **검증 케이스**: 5
- **차단 의존성**: `strength`(통근·합충 영향), `geokguk`(합거) 가 참조

---

## 🟡 정책 의존 중간 (default로 진행 가능, 자문위원 확정 권장)

### `solar_time.py` — 진태양시 보정
- **시그니처**: `correct_solar_time(dt, longitude, policy) -> datetime`
- **policy 의존**: `SolarTimePolicy` (default `WITH_EOT`)
- **검증 케이스**: 5 (보정 후 시각)
- **차단 의존성**: `pillars`

### `jeolgi.py` — 24절기 (특히 12절)
- **시그니처**: `get_jeolgi_boundaries(year, policy) -> list[JeolgiPoint]` / `month_branch_for(dt, policy) -> str`
- **policy 의존**: `WoljuBoundaryPolicy`(default `JEOL`), `SesuPolicy`(default `IPCHUN`)
- **검증 케이스**: 10 (절입 시각)
- **차단 의존성**: `pillars`, `daewoon`

### `pillars.py` — 사주 4기둥 추출 ★
- **시그니처**: `build_pillars(birth: BirthInfo, policy) -> FourPillars`
- **policy 의존**: `SolarTimePolicy`, `JasiPolicy`, `DayChangePolicy`, `WoljuBoundaryPolicy`, `SesuPolicy`, `LeapMonthPolicy`, `UnknownHourPolicy`, `LunarInputPolicy` (사실상 전부)
- **검증 케이스**: **30+ (8자 100% 일치 — 가장 중요)**
- **차단 의존성**: 사실상 모든 하류 모듈

---

## 🔴 정책 의존 높음 (자문위원 정책 확정 + 검증 케이스 50건+ 필수)

### `strength.py` — 신강신약
- **시그니처**: `assess_strength(pillars, policy) -> StrengthResult`
- **policy 의존**: 득령/득지/득세 가중, 통근 기준 (자문위원 확정 필수)
- **검증 케이스**: 50+ (목표 일치율 95%)

### `geokguk.py` — 격국
- **시그니처**: `determine_geokguk(pillars, strength, policy) -> GeokgukResult`
- **policy 의존**: `GeokgukPriority`(default `TUCHUL_FIRST`), 외격 기준
- **검증 케이스**: 50+ (목표 90%)

### `yongsin.py` — 용신
- **시그니처**: `derive_yongsin(pillars, strength, geokguk, policy) -> YongsinResult`
- **policy 의존**: `YongsinMethod`(default `EOKBU`), 조후 보정
- **검증 케이스**: 50+ (목표 85%, 자문위원 검증)

---

## ⚫ 최종 (위 전부에 의존)

### `daewoon.py` — 대운
- **시그니처**: `build_daewoon(birth, pillars, policy) -> list[DaewoonPeriod]`
- **policy 의존**: `DaewoonCalc`(default `DAYS_DIV3`), 순행/역행(년간 음양×성별)
- **검증 케이스**: 20 (시작 나이·방향)

### `sewoon.py` — 세운·월운·일운
- **시그니처**: `build_sewoon(pillars, year, policy)` / `month_un` / `day_un`
- **policy 의존**: `JasiPolicy`, `DayChangePolicy`
- **검증 케이스**: 10

---

## 권장 진행 순서 (세션 단위)

| 세션 | 모듈 | 비고 |
|---|---|---|
| **N+1 (이번 세션)** | `jijanggan` + `ten_gods` | 🟢 정책 무관, 하류 다수가 의존 → 최우선 |
| N+2 | `five_elements` + `relations` | 🟢 정책 무관 (분기점은 중단·질의) |
| N+3 | `solar_time` + `jeolgi` | 🟡 default 진행, 천문 계산 검증 |
| N+4 | `pillars` | 🟡 ★ 8자 추출, 검증 케이스 30+ 동반 |
| N+5 | `strength` | 🔴 정책 확정 + 케이스 50+ 선결 |
| N+6 | `geokguk` | 🔴 정책 확정 선결 |
| N+7 | `yongsin` | 🔴 정책 확정 선결 |
| N+8 | `daewoon` + `sewoon` | ⚫ 통합·회귀 |

> N+1~N+2(🟢)를 진행하는 동안 **자문위원 영입 + 🟡/🔴 정책 확정 + 검증 케이스 수집**을 병행.
> 🟡/🔴 모듈은 정책 확정 또는 검증 케이스 충족 전에는 착수하지 않는다.

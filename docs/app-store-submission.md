# 자평(Japyeong) 앱스토어 제출 자료 — 복붙용

> 작성 2026-06-10. 앱 `com.japyeong.app` · 회사 주식회사 바틀(Bottletaste Inc.)
> 빌드는 로컬 EAS 빌드로 생성(무료 플랜 한도 우회). 아래는 대표님이 콘솔에 그대로 넣을 값.

---

## 0. 먼저 해제할 블로커 (대표님만 가능)
1. **App Store Connect → 계약 → Apple Developer Program 사용권 계약 동의** (이거 없으면 iOS 제출 전부 막힘)
2. **Google Play Console → 앱 만들기 → "자평"** 레코드 생성 (현재 Play엔 자평 없음)

---

## 1. 공통 메타데이터

| 필드 | 값 |
|---|---|
| 앱 이름 | 자평 |
| 부제(iOS, ≤30자) | 명리 기반 AI 의사결정 자문 |
| 프로모션 텍스트(iOS) | 큰 결정 앞에서, 고전 명리를 근거로 함께 생각합니다. 운세가 아닌 의사결정 자문. |
| 카테고리(1차) | 라이프스타일 |
| 카테고리(2차) | 참고 |
| 지원 URL | https://ja-pyeong.vercel.app/support.html |
| 마케팅 URL | https://ja-pyeong.vercel.app/ |
| 개인정보처리방침 URL | https://ja-pyeong.vercel.app/privacy.html |
| 연령 등급 | 4+ (iOS) / 전체이용가 (Play) |

### 키워드 (iOS, ≤100자, 쉼표 구분)
```
사주,명리,운세,사주풀이,궁합,택일,오늘의운세,띠별운세,AI사주,사주명리,결정,자문,사주팔자
```

### 설명 (iOS/Play 공통, 복붙)
```
자평은 명리학(命理學) 고전을 근거로, 큰 결정을 앞둔 당신과 함께 생각하는 AI 자문 서비스입니다.

운세를 단정하지 않습니다. 사주 명식을 분석하고, 고전 원문과 학파별 견해를 함께 제시해
'지금 이 결정에 참고할 흐름'을 정리해 드립니다.

• 명식(命式) 분석 — 사주팔자와 인생 흐름을 한눈에
• 결정 도우미 — 이직·창업·결혼·이사 등 큰 결정의 시점 검토
• 궁합·택일(擇日) — 관계와 좋은 날 고르기
• 일진 알림 — 주의 깊게 볼 구간 표시
• 모든 결과에 고전 출처와 학파별 견해 표기

자평의 자문은 결정의 참고 자료이며, 의학·법률·재무 결정을 대체하지 않습니다.

[구독 안내]
• 월 자동 갱신 구독. 구독은 App Store/Play 계정 설정에서 언제든 해지할 수 있습니다.
• 자세한 이용약관: https://ja-pyeong.vercel.app/terms.html
• 환불 정책: https://ja-pyeong.vercel.app/refund.html
```

### Play 전용
- 간단한 설명(≤80자): `명리 고전을 근거로 큰 결정을 돕는 AI 자문. 운세가 아닌 의사결정 자문.`

---

## 2. 구독 상품(IAP) 등록표

> App Store Connect: 기능 → 구독 / Play Console: 수익 창출 → 구독
> ⚠️ 스토어는 가격 **티어**라 정확히 4,083·12,417원이 안 됩니다 → 아래 권장가로.

| 항목 | Basic | Standard(추천) |
|---|---|---|
| 상품 ID (iOS·Play 동일) | `japyeong_basic_monthly` | `japyeong_standard_monthly` |
| 참조 이름(내부) | 자평 베이직 월 | 자평 스탠다드 월 |
| 표시 이름 | 자평 베이직 | 자평 스탠다드 |
| 기간 | 1개월 자동갱신 | 1개월 자동갱신 |
| 권장 가격 | **₩4,400/월** | **₩13,000/월** |
| 설명 | 명식 분석 + 일진 알림 + 월간 흐름 | AI 상담·결정 도우미 무제한 + 상세 통변 |

> 상품 ID는 코드(`src/lib/iap.ts`)와 정확히 일치해야 합니다. 변경 시 코드도 같이 수정.
> 가격 확정 시 알려주시면 웹/회신서 금액도 일괄 정렬하겠습니다.

---

## 3. 앱 심사 노트 (App Review / Play 검토자에게)
```
- 테스트 계정: [대표님이 생성한 심사용 이메일/비번 입력]
- 로그인: 이메일+비밀번호. 첫 화면 → '로그인'.
- 구독 결제: 앱 내 결제는 Apple App Store / Google Play 인앱결제(StoreKit/Play Billing)만 사용합니다.
  (웹사이트 ja-pyeong.vercel.app 의 카카오페이 결제는 웹 전용이며 앱과 분리되어 있습니다.)
- 본 앱은 명리학 기반 정보·자문 서비스로, 결과를 단정하지 않으며 참고용임을 앱 내 명시합니다.
```

---

## 4. 빌드 업로드 (빌드 완료 후)
로컬 빌드 산출물: `/tmp/japyeong-android.aab` (Android)

**Android (Play Console)**
- 비공개 테스트 또는 프로덕션 트랙 → 새 버전 → `japyeong-android.aab` 업로드
- 또는 서비스계정 키 발급 후: `eas submit -p android --path /tmp/japyeong-android.aab`

**iOS** (계약 동의 후)
- `eas build -p ios --profile production` (대표님 Apple 로그인·2FA) → `eas submit -p ios`
- 또는 로컬 빌드 후 Transporter로 업로드

---

## 5. 운영 영수증 검증 키 (Vercel 백엔드 env)
- `APPLE_IAP_SHARED_SECRET` — App Store Connect → 앱 → 앱 전용 공유 비밀
- `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` — Play 서비스계정 (미설정 시 dev-accept)

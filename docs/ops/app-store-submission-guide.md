# 자평 앱스토어 제출 가이드 — v1.0.0

> **목적**: iOS App Store + Google Play Store에 자평 v1.0.0 제출
> **현재 상태**: 모든 코드·설정·아이콘·스플래시 준비 완료. 대표님이 직접 해야 할 외부 작업만 남음.
> **소요**: 계정 가입 후 평균 **iOS 1~2일 / Android 6시간** 심사 (2026년 기준)

---

## 0. 전체 흐름 (한 페이지)

```
[1] 계정 가입       Apple Developer ($99/년) + Google Play ($25 1회)
       ↓
[2] 앱 등록         App Store Connect + Play Console에 자평 앱 생성
       ↓
[3] EAS 셋업        eas login + eas init + eas build:configure
       ↓
[4] 프로덕션 빌드   eas build --platform ios | android
       ↓
[5] 메타데이터      앱 설명, 스크린샷, 카테고리, 등급, 가격
       ↓
[6] 제출            eas submit 또는 콘솔에서 수동 업로드
       ↓
[7] 심사 → 출시     iOS 1~2일, Android 6시간 → 검토 → 출시 버튼
```

---

## 1. 외부 계정 가입 (대표님 직접)

### 1.1 Apple Developer Program ($99/년)
- URL: https://developer.apple.com/programs/enroll/
- 개인/법인 선택 가능 (법인이면 D-U-N-S 번호 필요, 1~2주 발급)
- **법인 명의 권장** (자평 = Bottle Inc.) — 추후 양도·매각·세금 처리 명확
- 결제 후 24~48시간 검증
- 이메일·국가·전화·주소 모두 카드 명의와 일치해야 함

### 1.2 Google Play Developer Account ($25 1회)
- URL: https://play.google.com/console/signup
- 개인 vs 조직 선택
- 본인 인증 (D-U-N-S 또는 본인 신원 증명)
- 결제 즉시 활성화 (보통 1~3일 검증)

### 1.3 (선택) D-U-N-S 번호 — 법인 가입 시
- https://www.dnb.com/duns-number/get-a-duns.html
- 무료, 1~2주 소요
- 한국 사업자등록증 + 법인등기부등본 필요

---

## 2. 앱 등록 (콘솔 상에서 빈 앱 생성)

### 2.1 App Store Connect (iOS)
1. https://appstoreconnect.apple.com 접속
2. **My Apps → ⊕ → New App**
3. 입력:
   - **Platform**: iOS
   - **Name**: 자평 (子平)
   - **Primary Language**: Korean
   - **Bundle ID**: `com.japyeong.app` (이미 등록 안 됐으면 Identifier 먼저 등록)
   - **SKU**: `japyeong-ios-v1`
   - **User Access**: Full Access
4. **App Information**:
   - Subtitle: "결정 앞에, 자평"
   - Category Primary: Lifestyle
   - Category Secondary: Reference
   - Content Rights: 자평이 직접 작성 (✓)

### 2.2 Google Play Console (Android)
1. https://play.google.com/console 접속
2. **앱 만들기**
3. 입력:
   - **앱 이름**: 자평
   - **기본 언어**: 한국어
   - **앱 또는 게임**: 앱
   - **무료/유료**: 무료 (인앱 결제는 별도 정책)
4. **앱 콘텐츠** 섹션 작성 (개인정보, 데이터 안전, 광고, 콘텐츠 등급 등)

---

## 3. EAS 셋업 (대표님 + 개발자)

### 3.1 EAS CLI 로그인
```bash
cd /Users/seungsoohan/Projects/JaPyeong/mobile
npm install -g eas-cli
eas login
# → expo 계정 (없으면 https://expo.dev 가입, 무료)
```

### 3.2 프로젝트 init
```bash
cd /Users/seungsoohan/Projects/JaPyeong/mobile
eas init --id PLACEHOLDER
# → EAS가 자동으로 projectId 발급 → app.json 의 extra.eas.projectId 자동 갱신
```

### 3.3 의존성 설치
```bash
cd /Users/seungsoohan/Projects/JaPyeong/mobile
npm install
# expo-font, expo-splash-screen 자동 설치됨 (package.json 에 이미 추가)
```

### 3.4 빌드 자격증명 설정 (자동)
```bash
eas credentials
# → iOS: Apple ID 입력하면 EAS가 자동으로 인증서·프로비저닝 생성·관리
# → Android: EAS가 자동으로 keystore 생성·관리 (잃어버리면 절대 같은 패키지로 업데이트 불가하니 백업)
```

---

## 4. 프로덕션 빌드 (EAS Cloud — 로컬 Xcode/Android Studio 불필요)

### 4.1 iOS 빌드
```bash
cd /Users/seungsoohan/Projects/JaPyeong/mobile
npm run build:ios
# 또는: eas build --platform ios --profile production
```
- 약 15~25분 소요
- 완료 후 `.ipa` 파일 다운로드 링크 + EAS 콘솔에서 확인

### 4.2 Android 빌드
```bash
npm run build:android
# 또는: eas build --platform android --profile production
```
- 약 10~15분 소요
- `.aab` (Android App Bundle) 생성

### 4.3 빌드 전 미리보기 (선택 권장)
```bash
npm run build:preview
# → 내부 테스터에게 설치 링크 발송 가능 (실기기 테스트용)
```

---

## 5. 앱스토어 메타데이터 (스크린샷·설명·키워드)

### 5.1 필수 스크린샷
| 플랫폼 | 사이즈 | 매수 |
|---|---|---|
| iOS 6.7" (iPhone 14 Pro Max) | 1290×2796 | 최소 3, 권장 6 |
| iOS 6.5" (iPhone 11 Pro Max) | 1242×2688 | 선택 |
| iOS 5.5" (iPhone 8 Plus) | 1242×2208 | 선택 (단, 13.0 이하 지원 시 필수) |
| Android Phone | 1080×1920 또는 비례 | 최소 2, 권장 8 |
| Android Feature Graphic | 1024×500 | 필수 1 |

**제작 방법** (가장 빠름):
1. Safari/Chrome 개발자 도구 → iPhone 14 Pro Max 시뮬레이트 (390×844 × 3x = 1170×2532, 비율 맞춤)
2. https://ja-pyeong.vercel.app/app 접속
3. 각 화면(Landing, Onboarding, Saju, Chat, Compatibility, Decision) 캡처
4. 또는 Figma에서 1290×2796 캔버스에 텍스트·기능 강조 오버레이 추가

### 5.2 앱 설명 (App Store Connect / Play Console 입력용)

**Subtitle / 짧은 설명** (30자):
```
결정 앞에, 자평 — 명리 자문 도구
```

**Description** (4000자, App Store Connect → "Description"):
```
자평(子平)은 900년 명리학 고전과 AI 보조 해석이 함께하는 사주 자문 도구입니다.

▶ 자평은 점이 아닙니다. 의사결정 자문입니다.
"맞다·안 맞다"를 약속하지 않습니다. 사주 8글자가 보여 주는 결의 방향을 정직하게 짚어 드리는 도구입니다.

▶ 3층 구조 — 다른 사주 앱과 결정적으로 다른 점
1. 결정론적 명리 엔진: 절기·진태양시·60갑자·격국·용신·대운을 코드가 먼저 확정합니다. AI가 사주를 푸는 게 아닙니다.
2. AI 보조 고전 해석: 연해자평·삼명통회·적천수 등 명리 고전을 출처와 함께 인용합니다. 학파별 견해가 갈리는 부분은 솔직하게 표시합니다.
3. 명리 자문위원 (Premium): 사람 자문위원이 1:1로 검토합니다.

▶ 라이브 기능
• 사주 명식 분석 (8자·십성·오행·격국·용신)
• 인생 흐름 그래프 — 대운 80년 길흉 시각화
• 12 카테고리 AI 자문 — 직업·결혼·자녀·재정 등
• 궁합(宮合) — 두 사주 비교 + 학파별 견해
• 택일(擇日) — 좋은 날 찾기
• 결정 도우미(決) — A/B 두 선택지 사주 관점 비교

▶ 자평의 약속
• 의학·법률·재무 결정을 대체하지 않습니다 — 참고 자료입니다
• "100% 정확", "놓치면 손해" 같은 단정·공포 마케팅 금지
• 자동 갱신은 디폴트 OFF (opt-in)
• 결제 후 7일 이내 100% 환불 (전자상거래법 청약철회)

▶ 위기 키워드 대응
대화 중 자살·자해 키워드 감지 시 자살예방상담전화 1393 안내가 자동 노출됩니다.

▶ 문의
• 고객 지원: hello@japyeong.kr
• 전화 (평일 10–18시): 1577-0000
• 자문위원 매칭: advisor@japyeong.kr
```

**Keywords** (100자, iOS only, 쉼표 구분):
```
사주, 명리, 운세, 궁합, 택일, 대운, 자평, 명식, 결정, 자문, 인생, 흐름
```

**Promotional Text** (170자, iOS only):
```
결정 앞에 펼치는 명리 자문 도구. AI 보조 고전 해석 + 자문위원 1:1. 의사결정 자문이지 점이 아닙니다.
```

### 5.3 카테고리 / 등급 / 가격
| 항목 | 값 |
|---|---|
| Primary Category | Lifestyle |
| Secondary Category | Reference |
| Age Rating | 12+ (또는 17+) — 명리·점성 콘텐츠 |
| Price | Free (인앱 결제 별도 출시 후 추가) |
| In-App Purchases | 추후 Sprint 1-4 결제 도입 후 추가 |

### 5.4 필수 URL (Privacy + Support)
| 필드 | URL |
|---|---|
| Privacy Policy URL | https://ja-pyeong.vercel.app/privacy.html |
| Support URL | https://ja-pyeong.vercel.app/support.html |
| Marketing URL (선택) | https://ja-pyeong.vercel.app/ |

---

## 6. iOS 심사 통과를 위한 체크리스트

### 6.1 Apple Review Guidelines — 명리/점성 앱 관련
- **Guideline 5.5 (Disclaimer)**: "이 앱은 entertainment 목적이며 …" 명시 권장 → 자평은 이미 결과지 디스클레이머에 포함됨
- **Guideline 4.0 (Design)**: minimum functionality — 자평은 6개 기능 라이브로 안전
- **Guideline 1.1 (Objectionable Content)**: 자살 키워드 감지 + 1393 안내 — 이미 구현
- **Guideline 5.1.1 (Privacy)**: 개인정보 수집 시 privacy policy 링크 필수 — 이미 ✓

### 6.2 Sign in with Apple
- 현재 자평은 회원·로그인이 없음 → 해당 없음
- Sprint 1-2에 회원 도입 시: Apple 로그인 + 다른 SNS 로그인 1개 이상 필수

### 6.3 ITSAppUsesNonExemptEncryption
- app.json 의 ios.infoPlist 에 `false` 명시 ✓ (이미 설정됨)
- 자평은 HTTPS만 사용, 자체 암호화 없음

### 6.4 App Tracking Transparency
- 자평 v1.0.0은 광고 추적 안 함 → ATT 권한 요청 불필요
- 추후 광고 도입 시 NSUserTrackingUsageDescription 추가 필요

---

## 7. 제출

### 7.1 EAS Submit (가장 빠름)
```bash
cd /Users/seungsoohan/Projects/JaPyeong/mobile

# iOS — eas.json 의 submit.production.ios 에 Apple ID 채워 넣은 후
npm run submit:ios

# Android — Service Account 키 파일이 있어야 함 (Play Console → API access → Create new service account)
npm run submit:android
```

### 7.2 수동 업로드 대안
- iOS: Xcode → Application Loader (별도 설치) 또는 Transporter 앱
- Android: Play Console → 프로덕션 트랙 → 새 출시 → AAB 업로드

### 7.3 심사 정보 (App Review Information)
- 테스트 계정: 자평은 회원·결제가 v1.0.0에 없어 불필요
- Demo Account: 없음
- Review Notes:
```
자평은 사주 명리학 기반 의사결정 자문 도구입니다. 결과는 entertainment·자기성찰 참고용이며 미래를 단정하지 않습니다.
- 사주 8자 분석 + AI 보조 해석
- 학파별 견해를 함께 표시
- 자살·자해 키워드 감지 시 1393 자동 안내
- 회원·결제 v1.0.0에 없음 (v1.1.0 추가 예정)
```

---

## 8. 출시 후 (Day 1 ~ Week 1)

### 8.1 모니터링
- App Store Connect → Analytics
- Play Console → Statistics
- 신규 다운로드 / 크래시 / 별점

### 8.2 첫 별점 5건 확보
- 자평 뉴스레터 / 베타 사용자에게 "앱스토어에서 별점 부탁드립니다" 한정 발송
- 5건 모이면 첫 페이지 검색 노출 확률 ↑

### 8.3 v1.0.1 핫픽스 준비
- 크래시 / 버그 발견 시 EAS Update로 OTA 푸시 (네이티브 빌드 재제출 불필요)
- `eas update --channel production` 으로 즉시 배포 가능 (JS 번들 변경분만)

---

## 9. 비용 요약

| 항목 | 비용 | 주기 |
|---|---|---|
| Apple Developer Program | $99 (~13만 원) | 매년 |
| Google Play Developer | $25 (~3만 5천 원) | 1회 |
| EAS Build (Production tier) | $0 또는 $99/월 (대규모) | 월 30회 무료 |
| 도메인 (japyeong.kr — 선택) | ~2만 원/년 | 매년 |
| **총 1년차** | **약 16만 원** (도메인 제외) | — |

---

## 10. 자평 v1.0.0 제출 직전 최종 체크리스트

| ✓ | 항목 | 비고 |
|---|---|---|
| ☐ | Apple Developer Program 가입 완료 | $99 결제 |
| ☐ | Google Play Developer 가입 완료 | $25 결제 |
| ☐ | App Store Connect 자평 앱 생성 | Bundle ID com.japyeong.app |
| ☐ | Play Console 자평 앱 생성 | Package com.japyeong.app |
| ☐ | `eas init` 실행 → projectId 발급 + app.json 갱신 | mobile/ 디렉터리 |
| ☐ | `eas credentials` — iOS·Android 자동 셋업 | EAS가 처리 |
| ☐ | `npm run build:preview` — 실기기 테스트 통과 | 본인 + 베타 2~3명 |
| ☐ | 스크린샷 6장 준비 (1290×2796) | 디자인 OR 화면 캡처 |
| ☐ | 앱 설명·키워드 입력 (App Store + Play Console) | 위 5.2 참조 |
| ☐ | Privacy Policy URL 활성 확인 | /privacy.html |
| ☐ | Support URL 활성 확인 | /support.html |
| ☐ | `npm run build:ios` + `npm run build:android` 프로덕션 빌드 | 약 30분 |
| ☐ | `npm run submit:ios` + `npm run submit:android` | EAS 자동 제출 |
| ☐ | 심사 통과 → "Release" 클릭 | iOS 1~2일 / Android 6시간 |

---

## 부록 A · 제가(개발자) 이미 준비한 것

- ✅ `mobile/app.json` — version 1.0.0, bundleId, splash, icon, infoPlist 모두 설정
- ✅ `mobile/eas.json` — development/preview/production 3개 프로파일
- ✅ `mobile/assets/icon.png` (1024×1024)
- ✅ `mobile/assets/adaptive-icon.png` (1024×1024 Android)
- ✅ `mobile/assets/splash.png` (1284×2778)
- ✅ `mobile/assets/favicon.png` (48×48)
- ✅ `mobile/assets/fonts/PretendardVariable.ttf` (6.4MB, 한국 산스 폰트)
- ✅ `mobile/App.tsx` — `useFonts` + `SplashScreen` 로직
- ✅ `mobile/src/api/client.ts` — 네이티브 API base 프로덕션 자동 지정
- ✅ `web/privacy.html` v1.0.0 프로덕션 정책
- ✅ `web/support.html` 신규 고객 지원 페이지
- ✅ `package.json` — `build:ios`, `build:android`, `submit:*` 스크립트

## 부록 B · 대표님이 직접 해야 할 것

| # | 작업 | 비용 | 시간 |
|---|---|---|---|
| 1 | Apple Developer Program 결제 | $99 | 10분 |
| 2 | Google Play Developer 결제 | $25 | 10분 |
| 3 | (법인) D-U-N-S 번호 발급 | 무료 | 1~2주 |
| 4 | Expo 계정 가입 (무료) | 0 | 5분 |
| 5 | App Store Connect / Play Console 앱 생성 | 0 | 30분 |
| 6 | 스크린샷 디자인 (또는 외주) | 0~30만 | 1~3일 |
| 7 | 앱 설명·키워드 입력 (위 가이드 복붙) | 0 | 20분 |
| 8 | `eas login` + `eas init` 실행 | 0 | 10분 |
| 9 | 빌드 명령 실행 + 제출 | 0 | 30분 |
| 10 | 심사 대기 + Release 클릭 | 0 | 1~2일 |

---

작성: 2026-06-07 · 자평 운영팀
다음 갱신: v1.0.1 출시 시점

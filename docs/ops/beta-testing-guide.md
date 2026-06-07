# 자평 베타 테스트 가이드 — TestFlight (iOS) + Internal Testing (Android)

> **목적**: 정식 출시 전 실 기기·실 사용자로 자평 v1.0.0 검증
> **권장 흐름**: EAS preview 빌드 → TestFlight/Internal → 베타 1~2주 → 피드백 반영 → 프로덕션 빌드 → 정식 제출
> **타임라인**: 베타 셋업 1일 + 테스트 1~2주 + 피드백 수정 2~3일 = **총 약 2~3주**

---

## 0. 전체 흐름 (한 페이지)

```
[1] EAS preview 빌드           npm run build:preview  →  .ipa + .apk
       ↓
[2-i] iOS · TestFlight 업로드   eas submit --profile preview --platform ios
       ↓
[2-a] Android · Internal Testing   Play Console → 내부 테스트 트랙
       ↓
[3] 테스터 초대                  이메일·링크 발송
       ↓
[4] 베타 1~2주 + 피드백 수집     크래시 자동 / 설문 + 통화
       ↓
[5] 핫픽스 → 새 빌드 → 재배포    eas update OR eas build
       ↓
[6] 프로덕션 빌드 + 제출         npm run build:ios/android + submit
```

---

## 1. iOS · TestFlight 베타 테스트

### 1.1 두 가지 트랙
| 트랙 | 인원 | 심사 | 사용 시점 |
|---|---|---|---|
| **Internal Testing** | App Store Connect 사용자 (팀원·관리자) 최대 **100명** | ❌ 심사 없음. 즉시 가능 | 초기 1~2주 |
| **External Testing** | 외부 베타 테스터 최대 **10,000명** | ✅ Beta App Review (1~2일) | 인플루언서·체험단·실사용자 모집 |

→ 권장: **Internal로 시작 → 안정되면 External 확대**.

### 1.2 셋업 단계 (App Store Connect 콘솔)

#### 1.2.1 사전: EAS preview 빌드 생성
```bash
cd /Users/seungsoohan/Projects/JaPyeong/mobile
npm run build:preview
# → iOS .ipa 생성 (~20분)
```

빌드 완료 후 자동으로 EAS 콘솔에 .ipa 등록됨.

#### 1.2.2 EAS Submit로 TestFlight 업로드
```bash
eas submit --platform ios --profile preview
# eas.json submit.production.ios 의 appleId / ascAppId / appleTeamId 사용
# → TestFlight 에 자동 업로드 (15~30분 대기)
```

또는 수동 업로드: Transporter 앱 (Mac App Store에서 무료 설치) → .ipa 드래그.

#### 1.2.3 App Store Connect에서 빌드 확인
1. https://appstoreconnect.apple.com → 자평 → **TestFlight** 탭
2. **iOS 빌드** 섹션에 새 빌드 표시 (처리 중 → 처리 완료 약 30분)
3. **Export Compliance** 질문 답변:
   - "Does your app use encryption?" → **No** (자평은 HTTPS만 사용, 자체 암호화 없음, `ITSAppUsesNonExemptEncryption: false` 이미 설정됨)

### 1.3 Internal 테스터 초대

#### 1.3.1 사용자 등록 (한 번만)
1. App Store Connect → **Users and Access**
2. **Internal Testers** 그룹에 이메일 추가 (테스터의 **Apple ID 이메일**이어야 함)
3. 권한: "Developer" 또는 "Marketing" 등 자유

#### 1.3.2 빌드 배포
1. TestFlight → 빌드 클릭 → **그룹 추가** → 위에서 등록한 테스터 그룹 선택
2. 테스터에게 자동으로 이메일 + TestFlight 앱 푸시 발송
3. 테스터는 **TestFlight 앱** (App Store에서 무료) 설치 후 "사용 가능" 탭에서 자평 설치

### 1.4 External 테스터 초대 (확장)

#### 1.4.1 Beta App Review 제출
1. TestFlight → **App Information** → 다음 정보 채우기:
   - **Beta App Description**: 자평 베타 — 명리학 + AI 자문 도구. 의사결정 보조용.
   - **Email**: hello@japyeong.kr
   - **Privacy Policy URL**: https://ja-pyeong.vercel.app/privacy.html
   - **License Agreement**: Apple 기본 표준 약관 사용
2. **Beta App Review Information**:
   - Demo Account: 없음 (자평 v1.0.0에 회원 없음)
   - Notes: "사주 명리학 기반 의사결정 자문 도구. 결과는 참고용·미래 단정 안 함. 자살 키워드 감지 시 1393 안내 자동."
3. Submit for Review → 1~2일 심사 → 통과 시 External 테스터 모집 가능

#### 1.4.2 External 테스터 모집
- **개별 이메일 초대**: 최대 10,000명, 이메일 + TestFlight 앱
- **공개 링크**: 이메일 없이 누구나 가입 가능, 자평 일반 모집 시 권장
  - 링크 예: `https://testflight.apple.com/join/XXXXXXXX`
  - SNS·뉴스레터·블로그에 그대로 공유 가능

### 1.5 빌드 만료 (중요)
- TestFlight 빌드는 **90일 후 자동 만료**
- 90일마다 새 빌드 업로드 필요

---

## 2. Android · Internal Testing (Play Console)

### 2.1 트랙 종류
| 트랙 | 인원 | 심사 | 사용 시점 |
|---|---|---|---|
| **Internal Testing** | 최대 100명 (Google 그룹 또는 이메일 리스트) | ❌ 즉시 | 초기 |
| **Closed Testing (Alpha)** | 무제한, 이메일 리스트 | ✅ 간단 심사 | 중기 |
| **Open Testing (Beta)** | 무제한, Play Store 공개 | ✅ 심사 | 정식 출시 직전 |

### 2.2 셋업 단계

#### 2.2.1 EAS preview 빌드
```bash
cd /Users/seungsoohan/Projects/JaPyeong/mobile
npm run build:preview
# → Android .apk 생성
```

#### 2.2.2 Internal Testing 트랙에 업로드
**방법 A — EAS submit (자동)**
```bash
eas submit --platform android --profile preview --track internal
# (Service Account Key 파일 필요 — Play Console → API access)
```

**방법 B — 수동 업로드**
1. Play Console → 자평 → **테스트 → 내부 테스트**
2. **새 출시 만들기** → .apk 파일 업로드
3. **출시 노트** (한국어):
   ```
   자평 v1.0.0 베타 (내부 테스트)

   - 사주 명식 분석
   - 인생 흐름 그래프 (대운 80년)
   - 12 카테고리 AI 자문
   - 궁합 / 택일 / 결정 도우미
   - 한자 자동 병기 + hover

   피드백: hello@japyeong.kr
   ```
4. **저장 → 검토 → 출시**

#### 2.2.3 테스터 초대
1. Play Console → **테스터** 탭 → **이메일 목록 만들기**
2. 이메일 리스트 입력 (테스터의 Gmail 또는 Play Store 계정)
3. **참여 URL 복사** → 테스터에게 발송
4. 테스터가 URL 클릭 → "테스터 되기" 동의 → Play Store에서 자평 설치 가능

### 2.3 빌드 만료
- Play 내부 테스트 빌드는 **만료 없음** (Play Console에 영구 보관)
- 새 버전 출시 시 이전 버전 덮어쓰기

---

## 3. 베타 테스터 구성 권장

| 카테고리 | 인원 | 역할 |
|---|---|---|
| **사내** | 5~10명 | 핵심 기능 검증, 매일 사용 |
| **자문위원** | 3~5명 | 명리 콘텐츠 품질 검증 |
| **타겟 페르소나** | 10~20명 | 40~60대 여성, 결정 앞 사람 |
| **기술 베타** | 3~5명 | 개발자·디자이너, 크래시·UX 리포트 |
| **시드 인플루언서** | 2~3명 | 명리 유튜버·블로거, 자평 톤 평가 |
| **총** | **약 30명** | 다양한 관점 + 관리 가능 규모 |

### 3.1 모집 채널
1. **사내·자문위원**: 직접 메일 발송 (TestFlight 그룹 / Play 이메일 리스트)
2. **타겟 페르소나**: 자평 뉴스레터 (있다면) / 카페 모집 (네이버 카페 사주 관련)
3. **기술 베타**: 사주에 관심 있는 개발자 커뮤니티
4. **시드 인플루언서**: 직접 DM·메일

---

## 4. 베타 중 피드백 수집

### 4.1 자동 수집
| 채널 | 데이터 |
|---|---|
| **TestFlight 피드백** | 사용자 스크린샷 + 메모 (앱 안에서 흔들면 자동) |
| **Play Console 사전 출시 보고서** | 자동 크래시 / 호환성 / 성능 |
| **EAS Dashboard** | 빌드 사용량, 다운로드 수 |
| **Vercel Analytics** | API 콜 수, 에러율 |

### 4.2 수동 수집
| 방법 | 빈도 | 산출물 |
|---|---|---|
| **Google Form 설문** | 매주 1회 | NPS / 만족도 / 개선점 |
| **1:1 통화** | 핵심 5명 / 격주 | 30분 인터뷰 → 메모 |
| **Slack/카톡 채널** | 상시 | 즉각적 버그·UX 피드백 |
| **사용 로그 추적** | 매일 | 기능별 진입률·이탈률 |

### 4.3 베타 피드백 설문 템플릿
```
[자평 v1.0.0 베타 피드백]

1. 자평을 며칠 사용해 보셨나요?  □1~3일 □4~7일 □2주 이상
2. 가장 자주 사용한 기능은? (복수 선택)
   □명식 분석 □인생 흐름 □AI 자문 □궁합 □택일 □결정 도우미
3. 친구에게 자평을 추천할 가능성 (0~10): __
4. 자평을 한 단어로 표현하면?
5. 가장 마음에 든 부분?
6. 가장 불편했던 부분?
7. v1.1에 꼭 추가됐으면 하는 기능?
8. 한자가 잘 읽혔나요?  □매우 잘  □보통  □어려움
9. 결제 의향: 월 4,900원 Basic / 연 14만 Standard / 연 39만 Premium
10. 자유 의견:
```

---

## 5. 베타 → 정식 출시 전환

### 5.1 베타 종료 기준 (Go / No-Go)
| 항목 | 기준 |
|---|---|
| 크래시율 | ≤ 0.5% (Play Console 기준) |
| NPS | ≥ 30 |
| 핵심 기능 완수율 | 명식 → AI 자문 ≥ 70% |
| 한자 hover 사용률 | ≥ 40% (디자인 검증) |
| 자살 키워드 감지 정확도 | 100% (1393 자동 노출) |
| 정체성 위반 카피 발견 | 0건 (금지어 CI 통과) |

### 5.2 핫픽스 워크플로우
```
버그 발견 → GitHub Issue → 코드 수정
   ↓
- JS만 변경 → eas update --channel production  (즉시 OTA, 재제출 X)
- 네이티브 변경 → eas build + eas submit  (재제출 필요)
```

### 5.3 베타 → 프로덕션 빌드
```bash
cd /Users/seungsoohan/Projects/JaPyeong/mobile

# 프로덕션 빌드 (자동 버전 증가)
npm run build:ios
npm run build:android

# 정식 제출
npm run submit:ios       # → App Store Review
npm run submit:android   # → Play Console Production
```

---

## 6. 베타 운영 체크리스트

### 6.1 베타 시작 전
- [ ] EAS preview 빌드 성공
- [ ] TestFlight 빌드 처리 완료
- [ ] Play Console 내부 테스트 트랙 출시 완료
- [ ] 테스터 30명 이메일 리스트 확정
- [ ] 베타 환영 메일 + Google Form 설문 준비
- [ ] Slack/카톡 채널 개설 (피드백 상시)

### 6.2 베타 주 1회 점검
- [ ] TestFlight 피드백 확인
- [ ] Play Console 사전 출시 보고서 확인
- [ ] Vercel Analytics 에러율 확인
- [ ] 1:1 통화 5건 진행 + 메모
- [ ] 피드백 정리 → 우선순위 트래커 갱신

### 6.3 베타 종료 시
- [ ] Go/No-Go 6개 기준 모두 통과 확인
- [ ] 발견된 버그 모두 해결 또는 v1.0.1 핫픽스로 분리
- [ ] 베타 테스터 감사 메일 발송 + 정식 출시 첫 30일 무료 Premium 제공
- [ ] 프로덕션 빌드 + 정식 제출

---

## 7. 비용·시간 요약

| 항목 | 비용 | 시간 |
|---|---|---|
| EAS preview 빌드 (월 30회 무료) | $0 | 20분/빌드 |
| TestFlight 사용 | $0 (Apple Dev 포함) | — |
| Play Internal Testing | $0 (Play Dev 포함) | — |
| 테스터 모집 (자체) | $0 | 1~2일 |
| 베타 기간 | $0 | 1~2주 |
| 핫픽스 빌드 (3~5회 예상) | $0 | 4~8시간 |
| **총 추가 비용** | **$0** | **약 2~3주** |

---

## 8. 자평 베타 v1.0.0 특별 고려사항

### 8.1 자평 정체성 검증 항목
베타 동안 다음을 반드시 확인:
1. **단정 표현 0건** — 모든 자문 응답에서 "반드시·정확히·100%" 없음
2. **학파 견해 자동 표시** — 격국·용신 답변에 contested 필드 채워짐
3. **고전 인용 자동 표시** — 모든 자문 답변에 citation 1건+
4. **자살 키워드 감지** — 테스터에게 "최근 너무 힘들다" 등 입력 시 1393 자동 노출 검증
5. **한자 자동 병기** — 모든 한자 토큰이 한글(漢字) 형식
6. **자녀 사주 상품 미노출** — 6개월 보류 약속 지켜짐

### 8.2 자문위원 베타 (별도 트랙)
Sprint 5-6에 자문위원 영입 후:
- 자문위원 5명에게 Premium 패키지 무료 제공
- 자문위원 1:1 매칭 시스템 검증
- 자문위원 → 사용자 피드백 루프 검증
- 자문위원이 작성한 답변 톤이 자평 정체성과 일치하는지

---

**작성**: 2026-06-07 · 자평 운영팀
**다음 갱신**: 첫 베타 라운드 종료 후

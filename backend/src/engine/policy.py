"""명리 엔진 정책 플래그.

⚠️  SSOT 동기화 규칙
────────────────────────────────────────────────────────────────
이 파일의 enum/default는 backend/docs/myeongri-policy.md 와 1:1 대응한다.
**여기서 default를 바꾸면 myeongri-policy.md의 해당 항목과 "변경 이력"도
반드시 함께 수정**한다. 문서와 코드가 어긋나면 정책 결정이 추적 불가해진다.
────────────────────────────────────────────────────────────────

현재 모든 default는 잠정값(자문위원 미확정)이다. 가장 일반적·검증된 정책을
보수적으로 골라 TBD 상태에서도 엔진이 동작하게 한다.

모든 엔진 모듈은 MyeongriPolicy 인스턴스를 인자로 받아 동작해야 한다
(전역 상태에 의존 금지 → 결정론성·테스트 용이성 보장).
"""

from dataclasses import dataclass, field
from enum import StrEnum


class SolarTimePolicy(StrEnum):
    """1. 진태양시 보정."""

    LONGITUDE_ONLY = "longitude_only"  # 경도차만
    WITH_EOT = "with_eot"  # 경도차 + 균시차


class JasiPolicy(StrEnum):
    """2. 자시(子時) 분할."""

    UNIFIED = "unified"  # 23~01시 단일 자시
    SPLIT = "split"  # 야자시/조자시 분리


class SesuPolicy(StrEnum):
    """3. 세수(歲首) 기준."""

    IPCHUN = "ipchun"  # 입춘세수
    DONGJI = "dongji"  # 동지세수


class WoljuBoundaryPolicy(StrEnum):
    """4. 월주 경계."""

    JEOL = "jeol"  # 12절 기준
    JUNGGI = "junggi"  # 12중기 기준


class LeapMonthPolicy(StrEnum):
    """5. 윤달 처리."""

    BY_JEOLGI = "by_jeolgi"  # 절기로 결정(윤달 무관)
    SEPARATE = "separate"  # 윤월 별도


class DayChangePolicy(StrEnum):
    """6. 일주 변경 시점."""

    MIDNIGHT = "midnight"  # 00:00 자정
    JASI = "jasi"  # 23:00 자시 시작


class GeokgukPriority(StrEnum):
    """7. 격국 판별 우선순위."""

    TUCHUL_FIRST = "tuchul_first"  # 천간 투출 우선
    BONGI_FIRST = "bongi_first"  # 월지 본기 우선


class YongsinMethod(StrEnum):
    """8. 용신 도출."""

    EOKBU = "eokbu"  # 억부 중심(조후 보조)
    JOHU = "johu"  # 조후 중심
    HYBRID = "hybrid"  # 억부·조후·통관·병약 종합


class SinsalScope(StrEnum):
    """9. 신살 채택 범위."""

    TWELVE_ONLY = "twelve_only"  # 12신살만
    EXTENDED = "extended"  # 12신살 + 길흉신


class DaewoonCalc(StrEnum):
    """10. 대운 산출."""

    DAYS_DIV3 = "days_div3"  # 절입 일수 ÷ 3
    JEOLGI_PROPORTIONAL = "jeolgi_proportional"  # 절입 시각 비례


class UnknownHourPolicy(StrEnum):
    """11. 출생시 미상 처리."""

    EXCLUDE = "exclude"  # 시주 제외(삼주 분석)
    ESTIMATE = "estimate"  # 12시간 추정


class LunarInputPolicy(StrEnum):
    """12. 음력 입력."""

    ACCEPT = "accept"  # 음력 받음 + 양력 변환
    REJECT = "reject"  # 양력만


@dataclass(frozen=True, slots=True)
class MyeongriPolicy:
    """엔진 동작을 결정하는 명리 정책 묶음.

    필드 default는 myeongri-policy.md 요약 표의 '코드 기본값'과 일치한다.
    frozen → 한 번 만든 정책은 불변(결정론성 보장).
    """

    solar_time: SolarTimePolicy = SolarTimePolicy.WITH_EOT
    jasi: JasiPolicy = JasiPolicy.UNIFIED
    sesu: SesuPolicy = SesuPolicy.IPCHUN
    wolju_boundary: WoljuBoundaryPolicy = WoljuBoundaryPolicy.JEOL
    leap_month: LeapMonthPolicy = LeapMonthPolicy.BY_JEOLGI
    day_change: DayChangePolicy = DayChangePolicy.MIDNIGHT
    geokguk_priority: GeokgukPriority = GeokgukPriority.TUCHUL_FIRST
    yongsin_method: YongsinMethod = YongsinMethod.EOKBU
    sinsal_scope: SinsalScope = SinsalScope.TWELVE_ONLY
    daewoon_calc: DaewoonCalc = DaewoonCalc.DAYS_DIV3
    unknown_hour: UnknownHourPolicy = UnknownHourPolicy.EXCLUDE
    lunar_input: LunarInputPolicy = LunarInputPolicy.ACCEPT

    # 음력→양력 변환·절기 라이브러리 식별자.
    # 잠정 채택 "sxtwl" (myeongri-policy.md 항목 12, 2026-05-21).
    lunar_converter: str | None = "sxtwl"

    # 정책 확정 추적: 항목명 → 확정 메모("2026-06-01 위원 OOO"). 미확정은 미포함.
    confirmed: dict[str, str] = field(default_factory=dict)


def get_default_policy() -> MyeongriPolicy:
    """현재 채택된 기본 정책(전 항목 잠정값, 자문위원 미확정).

    엔진 호출 시 명시적으로 정책을 넘기지 않는 경로의 기본값.
    """
    return MyeongriPolicy()

"""사주 8자 정확성 일회성 스팟체크 (테스트 아님).

목적: 검증 케이스 100건 게이트가 충족되기 전, 엔진의 8자 추출이
대략이라도 맞는지 독립적 기준으로 최소 확인한다.

검증 기준(출처)별 독립성:
  - 년주: 60갑자 공인 년주표 (1984년 = 甲子년). 보편 산술, 엔진/라이브러리와 무관 → 독립.
  - 일주: 공인 갑자일 anchor 2000-01-07 = 甲子. 거기서 60일 순환으로 직접 계산 →
          엔진은 일주를 sxtwl로 뽑으므로, 이 anchor 독립계산과의 대조가 가장 강한 신호.
  - 시주: 五鼠遁(연해자평 등 고전 공통 시간 천간 산출 규칙)을 본 스크립트에서 독립 구현.
  - 월주: sxtwl(寿星天文曆) getMonthGZ와 교차참조. 절입 시각은 동일 ephemeris 의존이나,
          월간(五虎遁)은 별도 계산 경로이므로 부분 독립.

주의:
  - 이 케이스들은 validation_cases/ 에 절대 넣지 않는다(자문위원 승인 전용).
  - 진태양시 보정을 끄기 위해 longitude=None으로 입력(시계시 = 비교 기준과 동일 기준).
  - 불일치가 나오면 임의 수정 금지 — 어느 기둥/모듈 문제인지 보고만.

실행: (backend/ 에서) python scripts/spot_check.py
"""

from __future__ import annotations

from datetime import date

import sxtwl

from src.engine.constants import CHUN_GAN, JI_JI
from src.engine.ganji import ganji_by_index
from src.engine.pillars import build_pillars
from src.engine.schema import BirthInfo

# 공인 anchor: 2000-01-07 = 甲子일 (널리 published)
_DAY_ANCHOR = date(2000, 1, 7)

# 시진 지지(子=23~01시 기준) — 시각→지지 index
def hour_branch_index(hour: int) -> int:
    return ((hour + 1) // 2) % 12


def expected_year_ganji(myeongri_year: int) -> tuple[str, str]:
    """공인 년주표: 1984=甲子 기준 (입춘 지난 명리 연도)."""
    return ganji_by_index((myeongri_year - 1984) % 60)


def expected_day_ganji(d: date) -> tuple[str, str]:
    """anchor(2000-01-07=甲子)에서 60일 순환 독립 계산."""
    return ganji_by_index((d - _DAY_ANCHOR).days % 60)


def expected_hour_ganji(day_gan: str, hour: int) -> tuple[str, str]:
    """五鼠遁 독립 구현: 子時 천간 = (2·(일간 index%5))%10, 시지만큼 진행."""
    di = CHUN_GAN.index(day_gan)
    ja_stem = (2 * (di % 5)) % 10
    hbi = hour_branch_index(hour)
    return CHUN_GAN[(ja_stem + hbi) % 10], JI_JI[hbi]


def sxtwl_month_ganji(d: date) -> tuple[str, str]:
    sd = sxtwl.fromSolar(d.year, d.month, d.day)
    gz = sd.getMonthGZ()
    return CHUN_GAN[gz.tg], JI_JI[gz.dz]


# 점검 케이스: 입춘 이후(3~11월)라 명리 연도 = 달력 연도. 시계시 기준(longitude 없음).
CASES = [
    # (연, 월, 일, 시, 분, 명리연도, 출처메모)
    (1984, 3, 15, 10, 0, 1984, "1984=甲子년 (공인 년주표)"),
    (2000, 6, 10, 14, 0, 2000, "2000=庚辰년; 일주 anchor 검증대상"),
    (2024, 5, 15, 12, 0, 2024, "2024=甲辰년"),
    (1990, 8, 20, 8, 0, 1990, "1990=庚午년"),
    (1955, 11, 11, 16, 0, 1955, "1955=乙未년 (KST 역사 +8:30 구간)"),
]


def fmt(g: tuple[str, str]) -> str:
    return g[0] + g[1]


def main() -> None:
    print("=" * 78)
    print("사주 8자 스팟체크 (독립 기준 대조, longitude=None=시계시)")
    print("=" * 78)
    all_match = True
    for y, m, d, hh, mm, myear, note in CASES:
        birth = BirthInfo(
            gender="M", calendar="solar", year=y, month=m, day=d,
            hour=hh, minute=mm, longitude=None, timezone="Asia/Seoul",
        )
        p = build_pillars(birth)
        eng = {
            "년": (p.year.gan, p.year.ji),
            "월": (p.month.gan, p.month.ji),
            "일": (p.day.gan, p.day.ji),
            "시": (p.hour.gan, p.hour.ji) if p.hour else ("—", "—"),
        }
        gd = date(y, m, d)
        exp = {
            "년": expected_year_ganji(myear),       # 독립
            "월": sxtwl_month_ganji(gd),            # sxtwl 교차참조(월간 부분독립)
            "일": expected_day_ganji(gd),           # 독립(anchor 60일 순환)
            "시": expected_hour_ganji(p.day.gan, hh),  # 독립(五鼠遁)
        }
        print(f"\n■ {y}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}  [{note}]")
        for pos in ("년", "월", "일", "시"):
            ok = eng[pos] == exp[pos]
            all_match = all_match and ok
            mark = "✓" if ok else "✗ 불일치"
            basis = {"년": "독립", "월": "sxtwl참조", "일": "독립anchor", "시": "독립五鼠遁"}[pos]
            print(f"   {pos}주  엔진 {fmt(eng[pos]):<6} | 기준 {fmt(exp[pos]):<6} [{basis}]  {mark}")
    print("\n" + "=" * 78)
    print("결과:", "전건 일치 ✓" if all_match else "불일치 존재 ✗ — 보고 필요(임의 수정 금지)")
    print("=" * 78)


if __name__ == "__main__":
    main()

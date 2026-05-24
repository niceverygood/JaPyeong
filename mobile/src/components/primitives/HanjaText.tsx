/**
 * HanjaText — '한글(한자)' 패턴을 인식해서 hover 툴팁을 붙여 주는 Text.
 *
 * 백엔드 glossary.py가 모든 한자 토큰을 '한글(漢字)' 형식으로 병기해 보낸다.
 * 이 컴포넌트는 그 패턴을 찾아 각 단어 위에 hover 시 의미가 뜨는 inline 영역을 만든다.
 *
 * - Web: HTML `title` 속성으로 네이티브 툴팁 (지연·접근성 기본 제공)
 * - Native: `accessibilityLabel`로 스크린 리더 안내 (시각적 툴팁은 없음 — Web 우선)
 *
 * 일반 <Text>와 인터페이스가 동일하지만 children은 string으로 한정한다.
 */

import { Text } from "react-native";
import type { TextProps } from "react-native";

import { lookupMeaning } from "@/lib/hanjaGlossary";

/** '한글(漢字)' 패턴 — 한글 1자+ 뒤에 (한자 1자+) */
const HANJA_INLINE_RE = /([가-힣]+)\(([一-鿿]+)\)/g;

type Segment =
  | { kind: "text"; text: string }
  | { kind: "hanja"; kor: string; han: string; meaning: string };

function splitSegments(text: string): Segment[] {
  const out: Segment[] = [];
  let lastIndex = 0;
  // 매 호출마다 lastIndex 초기화 (global 정규식 재사용 안전)
  HANJA_INLINE_RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = HANJA_INLINE_RE.exec(text)) !== null) {
    const kor = m[1];
    const han = m[2];
    if (kor === undefined || han === undefined) continue;
    if (m.index > lastIndex) {
      out.push({ kind: "text", text: text.slice(lastIndex, m.index) });
    }
    out.push({ kind: "hanja", kor, han, meaning: lookupMeaning(kor, han) });
    lastIndex = m.index + m[0].length;
  }
  if (lastIndex < text.length) {
    out.push({ kind: "text", text: text.slice(lastIndex) });
  }
  return out;
}

interface HanjaTextProps extends Omit<TextProps, "children"> {
  children: string;
  /** 한자 부분에 추가로 줄 className (기본: 점선 밑줄 + gold-light). */
  hanjaClassName?: string;
}

export function HanjaText({
  children,
  hanjaClassName = "text-gold-light",
  ...rest
}: HanjaTextProps) {
  const segments = splitSegments(children);

  // 한자 패턴이 없으면 그대로 Text 반환 (불필요한 nested span 방지)
  if (!segments.some((s) => s.kind === "hanja")) {
    return <Text {...rest}>{children}</Text>;
  }

  return (
    <Text {...rest}>
      {segments.map((seg, i) => {
        if (seg.kind === "text") {
          // 빈 문자열은 스킵 (불필요한 노드)
          if (!seg.text) return null;
          return <Text key={i}>{seg.text}</Text>;
        }
        // 한자 인라인 — Web에서는 title 속성으로 hover 툴팁
        return (
          <Text
            key={i}
            accessibilityLabel={seg.meaning}
            className={hanjaClassName}
            // Web 전용 title 속성. RN Native는 무시.
            // (TextProps에 title이 없어서 캐스팅)
            {...({ title: seg.meaning, dataSet: { tooltip: seg.meaning } } as object)}
          >
            {seg.kor}({seg.han})
          </Text>
        );
      })}
    </Text>
  );
}

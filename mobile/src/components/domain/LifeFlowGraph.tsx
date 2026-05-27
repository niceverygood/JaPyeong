/**
 * LifeFlowGraph — 대운 80년치 길흉 막대 그래프.
 *
 * 9 주기를 가로로 나열, 각 막대 높이는 |score| 비례, 색은 부호별:
 *   +대길/길  = gold-light
 *   평        = ink-muted
 *   -주의/흉  = ohaeng-hwa
 *
 * 클릭(터치) 시 그 주기의 reasons 가 toggle 표시됨.
 */

import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import type { LifeFlowPoint } from "@/api/types";
import { HanjaText } from "@/components/primitives/HanjaText";
import { colors } from "@/theme";

const BAR_AREA_HEIGHT = 110;
const MAX_ABS = 5;

function barColor(score: number): string {
  if (score >= 1.5) return colors.gold.light;
  if (score <= -1.5) return colors.ohaeng.hwa;
  return colors.text.muted;
}

function labelColor(score: number): string {
  if (score >= 1.5) return colors.gold.primary;
  if (score <= -1.5) return colors.ohaeng.hwa;
  return colors.text.secondary;
}

export function LifeFlowGraph({ points }: { points: LifeFlowPoint[] }) {
  const [selected, setSelected] = useState<number | null>(null);

  if (points.length === 0) {
    return (
      <Text className="font-sans text-xs text-ink-muted">
        대운 데이터가 없어 인생 흐름을 그릴 수 없습니다.
      </Text>
    );
  }

  const sel = selected != null ? points.find((p) => p.sequence === selected) : null;

  return (
    <View>
      {/* 중앙선이 0, 위로 양수 / 아래로 음수 */}
      <View
        style={{ height: BAR_AREA_HEIGHT }}
        className="relative w-full overflow-hidden rounded-md bg-bg-card"
      >
        {/* 0 baseline */}
        <View
          className="absolute left-0 right-0 border-t border-line"
          style={{ top: BAR_AREA_HEIGHT / 2 }}
        />
        <View className="absolute inset-0 flex-row items-center">
          {points.map((p) => {
            const half = BAR_AREA_HEIGHT / 2;
            const ratio = Math.min(Math.abs(p.score) / MAX_ABS, 1);
            const barH = ratio * (half - 4);
            const isActive = selected === p.sequence;
            return (
              <Pressable
                key={p.sequence}
                onPress={() =>
                  setSelected((cur) => (cur === p.sequence ? null : p.sequence))
                }
                className="h-full flex-1 items-center justify-center"
              >
                <View className="absolute left-0 right-0" style={{ top: half - barH * (p.score >= 0 ? 1 : 0), height: barH }}>
                  <View
                    className="mx-auto"
                    style={{
                      width: isActive ? 16 : 12,
                      height: barH,
                      backgroundColor: barColor(p.score),
                      borderRadius: 3,
                      opacity: isActive ? 1 : 0.85,
                    }}
                  />
                </View>
                {/* 선택 표식 */}
                {isActive && (
                  <View
                    className="absolute -top-1 h-2 w-2 rounded-full"
                    style={{ backgroundColor: colors.gold.primary }}
                  />
                )}
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* 가로 축 라벨 — 나이 */}
      <View className="mt-2 flex-row">
        {points.map((p) => {
          const isActive = selected === p.sequence;
          return (
            <Pressable
              key={p.sequence}
              onPress={() =>
                setSelected((cur) => (cur === p.sequence ? null : p.sequence))
              }
              className="flex-1 items-center"
            >
              <Text
                className="font-sans text-[10px]"
                style={{ color: isActive ? colors.gold.primary : colors.text.muted }}
              >
                {p.start_age}
              </Text>
              <HanjaText
                hanjaClassName="text-gold-light"
                className="mt-0.5 font-serif text-xs"
              >
                {`${p.gan}${p.ji}`}
              </HanjaText>
              <Text
                className="mt-0.5 font-sans text-[10px]"
                style={{ color: labelColor(p.score) }}
              >
                {p.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {/* 선택된 주기의 사유 */}
      {sel && (
        <View className="mt-3 rounded-md border border-line bg-bg-card p-3">
          <View className="mb-1 flex-row items-baseline justify-between">
            <HanjaText className="font-serif text-base text-ink">
              {`${sel.start_age}~${sel.end_age}세 · ${sel.gan}${sel.ji}`}
            </HanjaText>
            <Text
              className="font-sans text-xs"
              style={{ color: labelColor(sel.score) }}
            >
              {sel.label} ({sel.score >= 0 ? "+" : ""}
              {sel.score.toFixed(1)})
            </Text>
          </View>
          {sel.reasons.length === 0 ? (
            <Text className="font-sans text-xs text-ink-muted">
              특별한 강·약 신호 없음.
            </Text>
          ) : (
            sel.reasons.map((r, i) => (
              <HanjaText
                key={i}
                className="font-sans text-xs leading-5 text-ink-secondary"
              >
                {`· ${r}`}
              </HanjaText>
            ))
          )}
        </View>
      )}

      <Text className="mt-2 text-center font-sans text-[10px] text-ink-muted">
        주기를 눌러 점수 근거 확인 · 잠정 · 자문위원 검증 전
      </Text>
    </View>
  );
}

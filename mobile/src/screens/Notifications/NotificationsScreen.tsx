/**
 * 알림 설정 화면 — 마이페이지 1depth.
 *
 * 자평 가드레일 (BM v2 정체성):
 *   - 켜기·끄기 모두 1 탭 (다크 패턴 차단)
 *   - 부정 통변 알림만 끄기 토글 별도 (불안 마케팅 방지)
 *   - 권한 상태·문제 사유 명확히 표시
 *   - "더 받기·할인" 같은 유인 카피 0건
 */

import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, Switch, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useUpdatePrefs } from "@/api/notifications";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { useDailyFortunePush } from "@/hooks/useDailyFortunePush";
import { colors } from "@/theme";

export function NotificationsScreen() {
  const push = useDailyFortunePush();
  const updatePrefs = useUpdatePrefs();

  // 사용자 설정 (서버 동기화는 Sprint 1-2 회원 도입 후)
  const [dailyEnabled, setDailyEnabled] = useState<boolean>(false);
  const [negativeMuted, setNegativeMuted] = useState<boolean>(false);
  const [time, setTime] = useState<string>("08:00");

  // 푸시 권한 상태 → daily 토글 동기화
  useEffect(() => {
    if (push.granted && !dailyEnabled) setDailyEnabled(true);
  }, [push.granted, dailyEnabled]);

  const onToggleDaily = async (next: boolean) => {
    if (next && !push.granted) {
      // 켜기 시 권한 요청 (사용자 명시적 액션)
      await push.requestAndRegister();
      return;
    }
    setDailyEnabled(next);
    try {
      await updatePrefs.mutateAsync({
        daily_fortune_enabled: next,
        daily_fortune_time_hhmm: time,
        negative_fortune_muted: negativeMuted,
      });
    } catch {
      // 백엔드 실패는 silent (로컬 상태는 유지)
    }
  };

  const onToggleNegativeMute = async (next: boolean) => {
    setNegativeMuted(next);
    try {
      await updatePrefs.mutateAsync({
        daily_fortune_enabled: dailyEnabled,
        daily_fortune_time_hhmm: time,
        negative_fortune_muted: next,
      });
    } catch {
      // silent
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-bg-base" edges={["bottom"]}>
      <ScrollView>
        <View className="p-5 gap-3">
          <View className="mb-2">
            <Text className="font-serif text-2xl text-ink">알림</Text>
            <Text className="mt-1 font-sans text-sm text-ink-secondary">
              일진 알림 · 부정 통변 끄기 · 발송 시간
            </Text>
          </View>

          {/* 일진 daily push 토글 */}
          <Card>
            <View className="flex-row items-center justify-between">
              <View className="flex-1 pr-3">
                <Text className="font-serif text-base text-ink">
                  일진 알림 받기
                </Text>
                <Text className="mt-1 font-sans text-xs text-ink-secondary">
                  매일 오늘 일진을 짧게 안내합니다. "주의 깊게 볼 구간" 톤으로만.
                </Text>
              </View>
              {push.loading ? (
                <ActivityIndicator color={colors.gold.primary} />
              ) : (
                <Switch
                  value={dailyEnabled && push.granted}
                  onValueChange={onToggleDaily}
                  trackColor={{ false: colors.line, true: colors.gold.primary }}
                  thumbColor={colors.text.primary}
                />
              )}
            </View>

            {/* 권한 거부 / 시뮬레이터 사유 */}
            {push.error && (
              <View className="mt-3 rounded-md border border-accent-brown bg-bg-card p-3">
                <Text className="font-sans text-xs text-ohaeng-hwa">
                  {push.error}
                </Text>
              </View>
            )}
          </Card>

          {/* 부정 통변만 끄기 (불안 마케팅 방지 — 자평 가드 #9) */}
          <Card>
            <View className="flex-row items-center justify-between">
              <View className="flex-1 pr-3">
                <Text className="font-serif text-base text-ink">
                  부정 통변 알림 끄기
                </Text>
                <Text className="mt-1 font-sans text-xs text-ink-secondary">
                  주의·흉 일진은 알림하지 않습니다. 평·길·대길만 받습니다.
                </Text>
              </View>
              <Switch
                value={negativeMuted}
                onValueChange={onToggleNegativeMute}
                trackColor={{ false: colors.line, true: colors.gold.primary }}
                thumbColor={colors.text.primary}
                disabled={!dailyEnabled}
              />
            </View>
          </Card>

          {/* 발송 시간 (Sprint 5-6 후 시간 피커 추가 — 지금은 표시만) */}
          <Card>
            <View className="flex-row items-center justify-between">
              <View>
                <Text className="font-serif text-base text-ink">발송 시간</Text>
                <Text className="mt-1 font-sans text-xs text-ink-secondary">
                  매일 이 시각에 알림이 발송됩니다.
                </Text>
              </View>
              <Text className="font-serif text-lg text-gold">{time}</Text>
            </View>
            <View className="mt-3 flex-row gap-2">
              {["07:00", "08:00", "12:00", "20:00"].map((t) => (
                <Button
                  key={t}
                  label={t}
                  variant={t === time ? "primary" : "ghost"}
                  onPress={() => setTime(t)}
                />
              ))}
            </View>
          </Card>

          {/* 정체성 안내 (자평 가드) */}
          <View className="mt-2 rounded-md bg-bg-card p-3 border border-line">
            <Text className="font-sans text-xs text-ink-muted leading-5">
              자평 알림은 "주의 깊게 볼 구간"을 짚는 톤만 사용합니다. "놓치면 손해" 같은
              불안 자극 카피는 사용하지 않습니다. 위기 키워드 감지 시 자살예방상담전화
              1393을 자동 안내합니다.
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

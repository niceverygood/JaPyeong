/**
 * Paywall — 무료 일일 한도 도달 시 표시.
 *
 * 트리거: API 429 + paywall 메시지 (ApiError.isPaywallTrigger)
 * 사용:
 *   const { paywall, showPaywall, hidePaywall } = usePaywall();
 *   onError: (e) => { if (e instanceof ApiError && e.isPaywallTrigger) showPaywall(e.retryAfter); }
 *
 * BM v2 4티어 + SKU 분리:
 *   - 무료 → Basic (월 4,083원/연 49,000원) self-serve
 *   - 무료 → Standard (월 12,416원/연 149,000원) self-serve
 *   - Premium/Family는 전화 상담 (1577-0000)
 *
 * 자평 정체성 가드레일:
 *   - 다크 패턴 금지: 명확한 닫기 버튼, 자동 결제 진행 X
 *   - "한도 = paywall" 정중한 안내, FOMO 카피 0건
 */

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Linking, Modal, Pressable, Text, View } from "react-native";

import { Button } from "./Button";

interface PaywallContextValue {
  showPaywall: (retryAfterSec?: number) => void;
  hidePaywall: () => void;
  isOpen: boolean;
}

const PaywallCtx = createContext<PaywallContextValue | null>(null);

export function PaywallProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{ open: boolean; retryAfter?: number }>({
    open: false,
  });

  const showPaywall = useCallback((retryAfterSec?: number) => {
    setState({ open: true, retryAfter: retryAfterSec });
  }, []);
  const hidePaywall = useCallback(() => setState({ open: false }), []);

  const value = useMemo<PaywallContextValue>(
    () => ({ showPaywall, hidePaywall, isOpen: state.open }),
    [showPaywall, hidePaywall, state.open],
  );

  return (
    <PaywallCtx.Provider value={value}>
      {children}
      <PaywallModal
        open={state.open}
        onClose={hidePaywall}
        retryAfterSec={state.retryAfter}
      />
    </PaywallCtx.Provider>
  );
}

export function usePaywall(): PaywallContextValue {
  const ctx = useContext(PaywallCtx);
  if (!ctx) throw new Error("usePaywall must be used within PaywallProvider");
  return ctx;
}

interface ModalProps {
  open: boolean;
  onClose: () => void;
  retryAfterSec?: number;
}

function PaywallModal({ open, onClose, retryAfterSec }: ModalProps) {
  const hoursUntilReset = retryAfterSec
    ? Math.max(1, Math.round(retryAfterSec / 3600))
    : null;

  return (
    <Modal
      visible={open}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable
        className="flex-1 items-center justify-center bg-black/70 px-6"
        onPress={onClose}
      >
        <Pressable
          className="w-full max-w-md rounded-2xl border border-gold bg-bg-elevated p-6"
          onPress={(e) => e.stopPropagation()}
        >
          {/* 헤더 — 한자 글리프 */}
          <View className="mb-4 items-center">
            <Text className="font-serif text-4xl text-gold">禮</Text>
            <Text className="mt-2 font-serif text-xl text-ink">오늘의 자문 한도</Text>
          </View>

          {/* 본문 — 정중한 안내, FOMO 없음 */}
          <Text className="text-center font-sans text-base leading-7 text-ink-secondary">
            오늘 무료로 드리는 자문을 모두 사용하셨습니다.
            {"\n"}
            {hoursUntilReset
              ? `약 ${hoursUntilReset}시간 후 다시 이용 가능합니다.`
              : "내일 다시 이용 가능합니다."}
          </Text>

          {/* 구독 안내 — 디스클레이머 + 결제 유도 */}
          <View className="mt-5 rounded-lg border border-line bg-bg-card p-4">
            <Text className="mb-2 font-serif text-sm text-gold-light">
              더 깊은 풀이를 원하시면
            </Text>
            <View className="gap-2">
              <View className="flex-row justify-between">
                <Text className="font-sans text-sm text-ink">
                  Basic · 일 20회
                </Text>
                <Text className="font-serif text-sm text-text">
                  연 49,000원
                </Text>
              </View>
              <View className="flex-row justify-between">
                <Text className="font-sans text-sm text-ink">
                  Standard · 일 100회 + 결정 도우미
                </Text>
                <Text className="font-serif text-sm text-text">
                  연 149,000원
                </Text>
              </View>
            </View>
            <Text className="mt-3 font-sans text-xs text-ink-muted">
              자동 갱신은 디폴트 OFF · 결제 후 7일 이내 100% 환불
            </Text>
          </View>

          {/* CTA — 결제 페이지 (웹 URL 또는 인앱 결제 — Sprint 1-2 후 활성) */}
          <View className="mt-4 gap-2">
            <Button
              label="요금제 자세히 보기"
              onPress={() => {
                Linking.openURL("https://ja-pyeong.vercel.app/#pricing");
                onClose();
              }}
            />
            <Button label="나중에 보기" variant="ghost" onPress={onClose} />
          </View>

          {/* 1:1 자문 안내 — 별도 CTA */}
          <View className="mt-4 border-t border-line pt-4">
            <Text className="text-center font-sans text-xs text-ink-muted">
              자문위원 1:1 (Premium/Family)은 전화 상담으로 신청합니다
            </Text>
            <Pressable
              onPress={() => {
                Linking.openURL("tel:1577-0000");
                onClose();
              }}
              className="mt-2 self-center"
            >
              <Text className="font-serif text-sm text-gold">1577-0000</Text>
            </Pressable>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

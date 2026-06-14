/** 회원 정보 + 로그아웃 + 회원 탈퇴.
 *
 * 가드:
 *   - 탈퇴는 confirm 모달 + 30일 보존 안내 (개인정보보호법)
 *   - 웹에선 Alert.alert 가 onPress 콜백을 호출하지 않으므로 window.confirm 분기
 *   - tier 는 한국어 매핑 (한국어 화면에 영문 raw 노출 X)
 */

import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useState } from "react";
import { Alert, Platform, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { deleteMe } from "@/api/auth";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import type { RootStackParamList } from "@/navigation/types";
import { useAuthStore } from "@/stores/authStore";

type Nav = NativeStackNavigationProp<RootStackParamList, "Profile">;

const TIER_KO: Record<string, string> = {
  anon: "무료",
  basic: "베이직",
  standard: "스탠다드",
  premium: "프리미엄",
  family: "패밀리",
};
function tierKo(t: string | undefined): string {
  return TIER_KO[t ?? "anon"] ?? (t ?? "무료").toUpperCase();
}

async function confirmAsync(title: string, message: string): Promise<boolean> {
  // 웹: window.confirm — RN-web 의 Alert.alert 는 onPress 콜백을 호출하지 않음.
  if (Platform.OS === "web" && typeof globalThis.confirm === "function") {
    return globalThis.confirm(`${title}\n\n${message}`);
  }
  return new Promise((resolve) => {
    Alert.alert(title, message, [
      { text: "취소", style: "cancel", onPress: () => resolve(false) },
      { text: "탈퇴", style: "destructive", onPress: () => resolve(true) },
    ]);
  });
}

async function alertAsync(title: string, message: string): Promise<void> {
  if (Platform.OS === "web" && typeof globalThis.alert === "function") {
    globalThis.alert(`${title}\n\n${message}`);
    return;
  }
  Alert.alert(title, message);
}

export function ProfileScreen() {
  const navigation = useNavigation<Nav>();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [deleting, setDeleting] = useState(false);

  const confirmDelete = async () => {
    const ok = await confirmAsync(
      "회원 탈퇴",
      "탈퇴 시 모든 데이터는 30일 후 완전 삭제됩니다 (개인정보보호법).\n진행하시겠습니까?",
    );
    if (!ok) return;
    setDeleting(true);
    try {
      await deleteMe();
      await logout();
      navigation.reset({ index: 0, routes: [{ name: "AuthLanding" }] });
    } catch (e) {
      await alertAsync("탈퇴 실패", e instanceof Error ? e.message : "다시 시도해주세요.");
    } finally {
      setDeleting(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigation.reset({ index: 0, routes: [{ name: "AuthLanding" }] });
  };

  return (
    <SafeAreaView className="flex-1 bg-bg-base">
      <ScrollView contentContainerStyle={{ paddingHorizontal: 24, paddingTop: 24, paddingBottom: 40 }}>
        <Text className="mb-6 font-serif text-2xl text-ink">내 정보</Text>

        <Card>
          <View className="gap-3 px-4 py-4">
            <View className="flex-row items-center justify-between">
              <Text className="font-sans text-sm text-ink-muted">이메일</Text>
              <Text className="font-sans text-base text-ink">{user?.email ?? "—"}</Text>
            </View>
            <View className="flex-row items-center justify-between">
              <Text className="font-sans text-sm text-ink-muted">이름</Text>
              <Text className="font-sans text-base text-ink">{user?.name ?? "—"}</Text>
            </View>
            <View className="flex-row items-center justify-between">
              <Text className="font-sans text-sm text-ink-muted">플랜</Text>
              <Text className="font-sans text-base text-gold">{tierKo(user?.tier)}</Text>
            </View>
          </View>
        </Card>

        <View className="mt-8 gap-3">
          <Button
            label="내 코인"
            onPress={() => navigation.navigate("Coins")}
          />
          <Button
            label="구독 플랜 보기"
            variant="ghost"
            onPress={() => navigation.navigate("Plans")}
          />
          <Button
            label="일진 알림 설정"
            variant="ghost"
            onPress={() => navigation.navigate("Notifications")}
          />
          <Button label="로그아웃" variant="ghost" onPress={handleLogout} />
        </View>

        <View className="mt-12">
          <Text className="mb-2 font-sans text-sm text-ink-muted">계정 관리</Text>
          <Button
            label={deleting ? "처리 중…" : "회원 탈퇴"}
            variant="ghost"
            onPress={confirmDelete}
            loading={deleting}
            accessibilityLabel={deleting ? "회원 탈퇴 처리 중" : "회원 탈퇴"}
          />
          <Text className="mt-3 font-sans text-xs text-ink-faint">
            탈퇴 시 30일 보존 후 완전 삭제됩니다 (개인정보보호법).
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

import { ActivityIndicator, Pressable, Text } from "react-native";

import { colors } from "@/theme";

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: "primary" | "ghost";
  loading?: boolean;
  disabled?: boolean;
  // 접근성: 로딩 중에도 라벨 유지 (스크린리더가 ActivityIndicator 못 읽음)
  accessibilityLabel?: string;
  accessibilityHint?: string;
  testID?: string;
}

export function Button({
  label,
  onPress,
  variant = "primary",
  loading = false,
  disabled = false,
  accessibilityLabel,
  accessibilityHint,
  testID,
}: ButtonProps) {
  const isDisabled = disabled || loading;
  const base =
    "h-14 items-center justify-center rounded-lg px-6 active:opacity-80";
  const styles =
    variant === "primary"
      ? "border border-gold bg-gold"
      : "border border-lineStrong bg-bg-raised";
  const textStyle = variant === "primary" ? "text-bg-base" : "text-gold";

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      testID={testID}
      onPress={onPress}
      disabled={isDisabled}
      className={`${base} ${styles} ${isDisabled ? "opacity-50" : ""}`}
    >
      {loading ? (
        <ActivityIndicator color={colors.bg.base} />
      ) : (
        <Text className={`font-sans text-base font-semibold ${textStyle}`}>
          {label}
        </Text>
      )}
    </Pressable>
  );
}

import { ActivityIndicator, Pressable, Text } from "react-native";

import { colors } from "@/theme";

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: "primary" | "ghost";
  loading?: boolean;
  disabled?: boolean;
}

export function Button({
  label,
  onPress,
  variant = "primary",
  loading = false,
  disabled = false,
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

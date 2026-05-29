import { Text, TextInput, View } from "react-native";

import { colors } from "@/theme";

interface FieldProps {
  label: string;
  value: string;
  onChangeText: (v: string) => void;
  placeholder?: string;
  keyboardType?: "default" | "number-pad";
}

export function Field({
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType = "default",
}: FieldProps) {
  return (
    <View className="mb-4">
      <Text className="mb-2 font-sans text-sm text-ink-secondary">{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.text.faint}
        keyboardType={keyboardType}
        className="h-12 rounded-lg border border-line bg-bg-card px-4 font-sans text-base text-ink"
      />
    </View>
  );
}

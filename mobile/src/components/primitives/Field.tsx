import { forwardRef } from "react";
import { Text, TextInput, View, type TextInputProps } from "react-native";

import { colors } from "@/theme";

interface FieldProps {
  label: string;
  value: string;
  onChangeText: (v: string) => void;
  placeholder?: string;
  // TextInput 의 표준 props — 보안·자동완성·접근성 풀 지원
  keyboardType?: TextInputProps["keyboardType"];
  secureTextEntry?: boolean;
  autoCapitalize?: TextInputProps["autoCapitalize"];
  autoCorrect?: boolean;
  autoComplete?: TextInputProps["autoComplete"];
  textContentType?: TextInputProps["textContentType"];
  returnKeyType?: TextInputProps["returnKeyType"];
  onSubmitEditing?: TextInputProps["onSubmitEditing"];
  blurOnSubmit?: boolean;
  // 접근성
  accessibilityLabel?: string;
  accessibilityHint?: string;
  // 인라인 에러 + touched gate (showError 가 true 일 때만 노출)
  error?: string;
  showError?: boolean;
  // 자동화 테스트 + 디버깅
  testID?: string;
}

export const Field = forwardRef<TextInput, FieldProps>(function Field(
  {
    label,
    value,
    onChangeText,
    placeholder,
    keyboardType = "default",
    secureTextEntry = false,
    autoCapitalize,
    autoCorrect,
    autoComplete,
    textContentType,
    returnKeyType,
    onSubmitEditing,
    blurOnSubmit,
    accessibilityLabel,
    accessibilityHint,
    error,
    showError,
    testID,
  },
  ref,
) {
  return (
    <View className="mb-4">
      <Text className="mb-2 font-sans text-sm text-ink-secondary">{label}</Text>
      <TextInput
        ref={ref}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.text.faint}
        keyboardType={keyboardType}
        secureTextEntry={secureTextEntry}
        autoCapitalize={autoCapitalize}
        autoCorrect={autoCorrect}
        autoComplete={autoComplete}
        textContentType={textContentType}
        returnKeyType={returnKeyType}
        onSubmitEditing={onSubmitEditing}
        blurOnSubmit={blurOnSubmit}
        accessibilityLabel={accessibilityLabel ?? label}
        accessibilityHint={accessibilityHint}
        testID={testID}
        className="h-12 rounded-lg border border-line bg-bg-card px-4 font-sans text-base text-ink"
      />
      {showError && error ? (
        <Text
          accessibilityLiveRegion="polite"
          className="mt-1 font-sans text-xs text-state-warning"
        >
          {error}
        </Text>
      ) : null}
    </View>
  );
});

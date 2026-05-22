import { View } from "react-native";
import type { ViewProps } from "react-native";

interface CardProps extends ViewProps {
  className?: string;
}

export function Card({ className = "", children, ...rest }: CardProps) {
  return (
    <View
      className={`rounded-2xl border border-line bg-bg-elevated p-4 ${className}`}
      {...rest}
    >
      {children}
    </View>
  );
}

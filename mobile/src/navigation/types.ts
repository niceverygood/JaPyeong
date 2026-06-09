export type RootStackParamList = {
  // 인증
  AuthLanding: undefined;
  Login: { provider?: "kakao" | "apple" } | undefined;
  Signup: undefined;
  Profile: undefined;

  // 결제
  Plans: undefined;
  Checkout: { plan: "basic" | "standard" | "premium" | "family"; provider: "toss" | "kakao" | "mock"; recurring?: boolean };
  PaymentResult: { payment_id: number; payment_key?: string; pg_token?: string };

  // 메인
  Landing: undefined;
  Onboarding: undefined;
  Saju: undefined;
  Chat: undefined;
  Compatibility: undefined;
  DateSelection: undefined;
  Decision: undefined;
};

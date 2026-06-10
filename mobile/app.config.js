/** app.json 확장 — 웹 빌드에서만 baseUrl 적용.
 *
 * 문제: experiments.baseUrl="/app" 이 app.json 에 있으면 iOS/Android
 *   네이티브 번들 임베드(export:embed)까지 asset 경로에 /app 이 끼어들어
 *   `app.app/app/assets/...` (ENOTDIR — app.app/app 은 실행 바이너리) 로
 *   mkdir 실패 → EAS 빌드 전체 실패.
 *
 * 해결: 웹 export 때만 JAPYEONG_WEB_BUILD=1 로 baseUrl 주입.
 *   (package.json build:web 스크립트가 설정)
 */

module.exports = ({ config }) => {
  if (process.env.JAPYEONG_WEB_BUILD === "1") {
    config.experiments = { ...(config.experiments ?? {}), baseUrl: "/app" };
  }
  return config;
};

"""애플리케이션 설정. .env에서 로드 (pydantic-settings)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://japyeong:japyeong@localhost:5432/japyeong"
    redis_url: str = "redis://localhost:6379/0"

    anthropic_api_key: str = ""
    anthropic_model_standard: str = "claude-sonnet-4-6"
    anthropic_model_light: str = "claude-haiku-4-5"
    anthropic_model_deep: str = "claude-opus-4-7"

    voyage_api_key: str = ""

    portone_api_secret: str = ""
    portone_store_id: str = ""
    kakao_cid: str = ""
    kakao_admin_key: str = ""

    jwt_secret: str = "change-me-in-production"
    jwt_expire_days: int = 30

    pii_encryption_key: str = ""

    # OAuth provider 토큰 검증을 아직 구현 안 했으므로,
    # placeholder OAuth 라우트는 dev/staging 에서만 노출.
    # production 에서는 반드시 false (실 SDK + 검증 구현 후 true 로).
    oauth_placeholder_enabled: bool = True


_JWT_INSECURE_DEFAULT = "change-me-in-production"


def _validate_production_secrets(settings: Settings) -> None:
    """프로덕션 환경에서 위험한 default 값을 즉시 감지.

    env != local 일 때:
      - jwt_secret 가 default 면 raise (토큰 위조 가능)
      - jwt_secret 길이 < 32 면 raise
      - oauth_placeholder_enabled=True 면 raise
        (실 OAuth SDK 구현 전 placeholder 라우트가 살아있으면 계정 탈취 가능)
    """
    if settings.env == "local":
        return
    if settings.jwt_secret == _JWT_INSECURE_DEFAULT:
        raise RuntimeError(
            f"JWT_SECRET 환경변수 미설정 — env={settings.env} 에서 default 값 사용 금지. "
            "openssl rand -base64 48 로 생성 후 환경변수 등록 필요.",
        )
    if len(settings.jwt_secret) < 32:
        raise RuntimeError(
            f"JWT_SECRET 길이가 너무 짧음 ({len(settings.jwt_secret)} < 32) — "
            "최소 32바이트 권장.",
        )
    if settings.oauth_placeholder_enabled:
        raise RuntimeError(
            f"OAUTH_PLACEHOLDER_ENABLED=true 인 채 env={settings.env} 배포 금지. "
            "실 OAuth SDK + provider 토큰 검증 구현 전까지 false 로 설정.",
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    _validate_production_secrets(settings)
    return settings

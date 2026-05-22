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


@lru_cache
def get_settings() -> Settings:
    return Settings()

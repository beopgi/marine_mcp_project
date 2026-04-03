"""Application configuration module."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven app settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Marine MCP Prototype", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    adapter_mode: str = Field(default="mock", alias="ADAPTER_MODE")

    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    llm_model: str = Field(default="gemini-1.5-flash", alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_base_url: str | None = Field(default=None, alias="LLM_BASE_URL")

    naver_client_id: str | None = Field(default=None, alias="NAVER_CLIENT_ID")
    naver_client_secret: str | None = Field(default=None, alias="NAVER_CLIENT_SECRET")


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton settings instance."""
    return Settings()
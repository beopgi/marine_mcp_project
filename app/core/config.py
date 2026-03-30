"""Application configuration module."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven app settings."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='Marine MCP Prototype', alias='APP_NAME')
    app_env: str = Field(default='dev', alias='APP_ENV')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')

    adapter_mode: str = Field(default='mock', alias='ADAPTER_MODE')

    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    openai_base_url: str | None = Field(default=None, alias='OPENAI_BASE_URL')
    openai_model: str = Field(default='gpt-4o-mini', alias='OPENAI_MODEL')


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton settings instance."""

    return Settings()

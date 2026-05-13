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

    db_enabled: bool = Field(default=False, alias="DB_ENABLED")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    db_location_table: str = Field(default="location_logs", alias="DB_LOCATION_TABLE")
    db_location_user_id_column: str = Field(default="user_id", alias="DB_LOCATION_USER_ID_COLUMN")
    db_location_clerk_id_column: str = Field(default="clerk_id", alias="DB_LOCATION_CLERK_ID_COLUMN")
    db_location_latitude_column: str = Field(default="latitude", alias="DB_LOCATION_LATITUDE_COLUMN")
    db_location_longitude_column: str = Field(default="longitude", alias="DB_LOCATION_LONGITUDE_COLUMN")
    db_location_region_column: str = Field(default="region", alias="DB_LOCATION_REGION_COLUMN")
    db_location_address_column: str = Field(default="address", alias="DB_LOCATION_ADDRESS_COLUMN")
    db_location_accuracy_column: str = Field(default="accuracy_m", alias="DB_LOCATION_ACCURACY_COLUMN")
    db_location_recorded_at_column: str = Field(default="recorded_at", alias="DB_LOCATION_RECORDED_AT_COLUMN")
    db_location_created_at_column: str = Field(default="created_at", alias="DB_LOCATION_CREATED_AT_COLUMN")

    kma_enabled: bool = Field(default=False, alias="KMA_ENABLED")
    kma_api_key: str | None = Field(default=None, alias="KMA_API_KEY")
    kma_base_url: str = Field(
        default="https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0",
        alias="KMA_BASE_URL",
    )
    kma_timeout_seconds: float = Field(default=5.0, alias="KMA_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton settings instance."""
    return Settings()
from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Estufa da varanda", alias="APP_NAME")
    app_env: Literal["development", "testing", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")

    api_base_url: str = Field(default="http://localhost", alias="API_BASE_URL")
    frontend_base_url: str = Field(
        default="http://localhost:5173", alias="FRONTEND_BASE_URL"
    )
    cors_origins: str = Field(default="", alias="CORS_ORIGINS")

    app_secret_key: str = Field(alias="APP_SECRET_KEY")
    access_token_secret: str = Field(alias="ACCESS_TOKEN_SECRET")
    refresh_token_secret: str = Field(alias="REFRESH_TOKEN_SECRET")

    access_token_expires_minutes: int = Field(
        default=15, alias="ACCESS_TOKEN_EXPIRES_MINUTES"
    )
    refresh_token_expires_days: int = Field(
        default=30, alias="REFRESH_TOKEN_EXPIRES_DAYS"
    )
    password_reset_expires_minutes: int = Field(
        default=30, alias="PASSWORD_RESET_EXPIRES_MINUTES"
    )

    database_url: str = Field(alias="DATABASE_URL")

    upload_base_path: str = Field(default="./uploads", alias="UPLOAD_BASE_PATH")
    max_upload_mb: int = Field(default=8, alias="MAX_UPLOAD_MB")
    allowed_image_extensions: str = Field(
        default="jpg,jpeg,png,webp", alias="ALLOWED_IMAGE_EXTENSIONS"
    )
    allowed_image_mime_types: str = Field(
        default="image/jpeg,image/png,image/webp", alias="ALLOWED_IMAGE_MIME_TYPES"
    )

    default_timezone: str = Field(default="America/Sao_Paulo", alias="DEFAULT_TIMEZONE")
    enable_admin_read_all_plants: bool = Field(
        default=True, alias="ENABLE_ADMIN_READ_ALL_PLANTS"
    )

    rate_limit_default: str = Field(default="200/hour", alias="RATE_LIMIT_DEFAULT")
    rate_limit_login_attempts: int = Field(default=5, alias="RATE_LIMIT_LOGIN_ATTEMPTS")
    rate_limit_login_window_minutes: int = Field(
        default=10, alias="RATE_LIMIT_LOGIN_WINDOW_MINUTES"
    )
    login_block_minutes: int = Field(default=15, alias="LOGIN_BLOCK_MINUTES")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str | None = Field(default=None, alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    climate_provider: str = Field(default="open_meteo", alias="CLIMATE_PROVIDER")
    climate_api_key: str | None = Field(default=None, alias="CLIMATE_API_KEY")
    climate_request_timeout_seconds: int = Field(
        default=10, alias="CLIMATE_REQUEST_TIMEOUT_SECONDS"
    )

    ai_provider_mode: str = Field(default="rules", alias="AI_PROVIDER_MODE")
    ai_provider_url: str | None = Field(default=None, alias="AI_PROVIDER_URL")
    ai_provider_key: str | None = Field(default=None, alias="AI_PROVIDER_KEY")
    ai_provider_model: str | None = Field(default=None, alias="AI_PROVIDER_MODEL")

    push_provider_mode: str = Field(default="log", alias="PUSH_PROVIDER_MODE")
    push_provider_key: str | None = Field(default=None, alias="PUSH_PROVIDER_KEY")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")
    secure_cookies: bool = Field(default=False, alias="SECURE_COOKIES")

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @computed_field
    @property
    def allowed_image_extensions_set(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.allowed_image_extensions.split(",")
            if item.strip()
        }

    @computed_field
    @property
    def allowed_image_mime_types_set(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.allowed_image_mime_types.split(",")
            if item.strip()
        }

    @computed_field
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

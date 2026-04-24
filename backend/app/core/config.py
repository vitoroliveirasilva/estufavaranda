from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ALLOWED_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
_ALLOWED_AI_PROVIDER_MODES = {"rules", "external"}
_ALLOWED_PUSH_PROVIDER_MODES = {"log", "external"}
_ALLOWED_CLIMATE_PROVIDERS = {"open_meteo"}
_ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item and item.strip()]


def _normalize_csv(value: str) -> str:
    return ",".join(_split_csv(value))


def _validate_http_url(value: str, *, field_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} deve ser uma URL HTTP/HTTPS válida.")
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(_PROJECT_ROOT / ".env"),
            str(_BACKEND_ROOT / ".env"),
        ),
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

    @field_validator(
        "app_name",
        "app_host",
        "database_url",
        "upload_base_path",
        mode="before",
    )
    @classmethod
    def _strip_required_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator(
        "smtp_host",
        "smtp_user",
        "smtp_password",
        "smtp_from_email",
        "climate_api_key",
        "ai_provider_url",
        "ai_provider_key",
        "ai_provider_model",
        "push_provider_key",
        mode="before",
    )
    @classmethod
    def _normalize_optional_strings(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("app_env", mode="before")
    @classmethod
    def _normalize_app_env(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator(
        "climate_provider", "ai_provider_mode", "push_provider_mode", mode="before"
    )
    @classmethod
    def _normalize_provider_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator(
        "cors_origins",
        "allowed_image_extensions",
        "allowed_image_mime_types",
        mode="before",
    )
    @classmethod
    def _normalize_csv_fields(cls, value: object) -> object:
        if isinstance(value, str):
            return _normalize_csv(value)
        return value

    @field_validator("api_base_url")
    @classmethod
    def _validate_api_base_url(cls, value: str) -> str:
        return _validate_http_url(value, field_name="API_BASE_URL")

    @field_validator("frontend_base_url")
    @classmethod
    def _validate_frontend_base_url(cls, value: str) -> str:
        return _validate_http_url(value, field_name="FRONTEND_BASE_URL")

    @field_validator("default_timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except Exception as exc:
            raise ValueError("DEFAULT_TIMEZONE inválido.") from exc
        return value

    @field_validator("app_port", "smtp_port")
    @classmethod
    def _validate_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("Porta deve estar entre 1 e 65535.")
        return value

    @field_validator(
        "access_token_expires_minutes",
        "refresh_token_expires_days",
        "password_reset_expires_minutes",
        "max_upload_mb",
        "rate_limit_login_attempts",
        "rate_limit_login_window_minutes",
        "login_block_minutes",
        "climate_request_timeout_seconds",
    )
    @classmethod
    def _validate_positive_integers(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Valor deve ser maior que zero.")
        return value

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        if value not in _ALLOWED_LOG_LEVELS:
            raise ValueError(
                f"LOG_LEVEL inválido. Use um destes valores: {', '.join(sorted(_ALLOWED_LOG_LEVELS))}."
            )
        return value

    @field_validator("ai_provider_mode")
    @classmethod
    def _validate_ai_provider_mode(cls, value: str) -> str:
        if value not in _ALLOWED_AI_PROVIDER_MODES:
            raise ValueError(
                f"AI_PROVIDER_MODE inválido. Use um destes valores: {', '.join(sorted(_ALLOWED_AI_PROVIDER_MODES))}."
            )
        return value

    @field_validator("push_provider_mode")
    @classmethod
    def _validate_push_provider_mode(cls, value: str) -> str:
        if value not in _ALLOWED_PUSH_PROVIDER_MODES:
            raise ValueError(
                f"PUSH_PROVIDER_MODE inválido. Use um destes valores: {', '.join(sorted(_ALLOWED_PUSH_PROVIDER_MODES))}."
            )
        return value

    @field_validator("climate_provider")
    @classmethod
    def _validate_climate_provider(cls, value: str) -> str:
        if value not in _ALLOWED_CLIMATE_PROVIDERS:
            raise ValueError(
                f"CLIMATE_PROVIDER inválido. Use um destes valores: {', '.join(sorted(_ALLOWED_CLIMATE_PROVIDERS))}."
            )
        return value

    @field_validator("allowed_image_extensions")
    @classmethod
    def _validate_allowed_image_extensions(cls, value: str) -> str:
        extensions = {item.lower() for item in _split_csv(value)}
        if not extensions:
            raise ValueError("ALLOWED_IMAGE_EXTENSIONS não pode estar vazio.")
        invalid = extensions - _ALLOWED_IMAGE_EXTENSIONS
        if invalid:
            raise ValueError(
                f"ALLOWED_IMAGE_EXTENSIONS contém valores não suportados: {', '.join(sorted(invalid))}."
            )
        return ",".join(sorted(extensions))

    @field_validator("allowed_image_mime_types")
    @classmethod
    def _validate_allowed_image_mime_types(cls, value: str) -> str:
        mime_types = {item.lower() for item in _split_csv(value)}
        if not mime_types:
            raise ValueError("ALLOWED_IMAGE_MIME_TYPES não pode estar vazio.")
        return ",".join(sorted(mime_types))

    @model_validator(mode="after")
    def _validate_cross_field_rules(self) -> "Settings":
        if self.app_env == "production" and self.app_debug:
            raise ValueError("APP_DEBUG não pode estar habilitado em produção.")

        if self.app_env == "production":
            for field_name in (
                "app_secret_key",
                "access_token_secret",
                "refresh_token_secret",
            ):
                value = getattr(self, field_name)
                if len(value) < 16:
                    raise ValueError(
                        f"{field_name.upper()} deve ter ao menos 16 caracteres em produção."
                    )

        if self.ai_provider_mode == "external":
            missing = [
                field_name
                for field_name in (
                    "ai_provider_url",
                    "ai_provider_key",
                    "ai_provider_model",
                )
                if not getattr(self, field_name)
            ]
            if missing:
                raise ValueError(
                    "AI provider externo requer configuração completa: "
                    + ", ".join(name.upper() for name in missing)
                    + "."
                )
            _validate_http_url(self.ai_provider_url or "", field_name="AI_PROVIDER_URL")

        if self.smtp_host and not self.smtp_from_email:
            raise ValueError(
                "SMTP_FROM_EMAIL é obrigatório quando SMTP_HOST estiver configurado."
            )

        if (
            self.cors_origins_list
            and "*" in self.cors_origins_list
            and len(self.cors_origins_list) > 1
        ):
            raise ValueError(
                'CORS_ORIGINS não pode misturar "*" com origens específicas.'
            )

        return self

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        return list(dict.fromkeys(_split_csv(self.cors_origins)))

    @computed_field
    @property
    def allowed_image_extensions_set(self) -> set[str]:
        return {item.lower() for item in _split_csv(self.allowed_image_extensions)}

    @computed_field
    @property
    def allowed_image_mime_types_set(self) -> set[str]:
        return {item.lower() for item in _split_csv(self.allowed_image_mime_types)}

    @computed_field
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()

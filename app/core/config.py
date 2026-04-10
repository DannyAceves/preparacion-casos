from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Case Prep API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    database_url: str = Field(alias="DATABASE_URL")
    alembic_database_url: str = Field(alias="ALEMBIC_DATABASE_URL")
    db_schema: str = Field(default="caseproces", alias="DB_SCHEMA")
    redis_url: str = Field(alias="REDIS_URL")
    frontend_app_url: str = Field(default="http://localhost:3000", alias="FRONTEND_APP_URL")
    local_storage_path: str = Field(default="/app/storage/uploads", alias="LOCAL_STORAGE_PATH")
    document_storage_backend: str = Field(default="local", alias="DOCUMENT_STORAGE_BACKEND")
    document_storage_path: str = Field(default="/app/storage/documents", alias="DOCUMENT_STORAGE_PATH")
    document_max_size_bytes: int = Field(default=10_485_760, alias="DOCUMENT_MAX_SIZE_BYTES")
    document_processing_auto_enqueue: bool = Field(default=True, alias="DOCUMENT_PROCESSING_AUTO_ENQUEUE")
    document_processing_queue_name: str = Field(default="document-processing", alias="DOCUMENT_PROCESSING_QUEUE_NAME")
    document_processing_max_attempts: int = Field(default=3, alias="DOCUMENT_PROCESSING_MAX_ATTEMPTS")
    document_processing_worker_poll_timeout: int = Field(
        default=5,
        alias="DOCUMENT_PROCESSING_WORKER_POLL_TIMEOUT",
    )
    tesseract_command: str = Field(default="tesseract", alias="TESSERACT_COMMAND")
    ocrmypdf_command: str = Field(default="ocrmypdf", alias="OCR_MYPDF_COMMAND")
    document_ocr_language: str = Field(default="eng+spa", alias="DOCUMENT_OCR_LANGUAGE")
    document_embedded_text_min_chars: int = Field(default=30, alias="DOCUMENT_EMBEDDED_TEXT_MIN_CHARS")
    document_allowed_mime_types: Annotated[list[str], NoDecode] = Field(
        default=[
            "application/pdf",
            "image/jpeg",
            "image/png",
        ],
        alias="DOCUMENT_ALLOWED_MIME_TYPES",
    )

    @field_validator("document_allowed_mime_types", mode="before")
    @classmethod
    def parse_document_allowed_mime_types(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if value not in allowed:
            raise ValueError(f"APP_ENV must be one of: {', '.join(sorted(allowed))}")
        return value

    @field_validator("document_max_size_bytes")
    @classmethod
    def validate_document_max_size_bytes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("DOCUMENT_MAX_SIZE_BYTES must be greater than zero")
        return value

    @field_validator("db_schema")
    @classmethod
    def validate_db_schema(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("DB_SCHEMA must not be empty")
        if not normalized.replace("_", "").isalnum() or not normalized[0].isalpha():
            raise ValueError("DB_SCHEMA must start with a letter and contain only letters, numbers, and underscores")
        return normalized

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.document_storage_backend != "local":
            raise ValueError("Only local document storage is currently supported")
        if self.app_env in {"staging", "production"} and self.app_debug:
            raise ValueError("APP_DEBUG must be false outside development/test")
        if self.app_env in {"staging", "production"} and self.frontend_app_url.startswith("http://"):
            raise ValueError("FRONTEND_APP_URL must use https in staging/production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

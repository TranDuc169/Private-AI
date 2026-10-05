from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    database_url: str
    jwt_secret: SecretStr = Field(min_length=32)
    access_token_minutes: int = Field(default=30, ge=1, le=120)
    storage_dir: Path = Path(__file__).resolve().parents[1] / "storage"
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    max_pdf_pages: int = Field(default=200, ge=1, le=1000)
    max_pdf_characters: int = Field(default=2_000_000, ge=1000, le=10_000_000)
    pdf_timeout_seconds: int = Field(default=30, ge=1, le=120)
    ollama_base_url: str = "http://127.0.0.1:11434"
    embedding_model: str = "bge-m3:latest"
    embedding_timeout_seconds: int = Field(default=120, ge=1, le=120)
    embedding_batch_size: int = Field(default=8, ge=1, le=16)
    max_document_chunks: int = Field(default=3000, ge=1, le=5000)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

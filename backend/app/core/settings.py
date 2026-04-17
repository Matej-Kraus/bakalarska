from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_URL = f"sqlite:///{(BACKEND_DIR / 'app.db').resolve()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TRAINERAPP_",
        env_file=str(BACKEND_DIR / ".env"),
    )

    secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60 * 24  # 24h
    database_url: str = DEFAULT_DB_URL

    frontend_base_url: str = "http://127.0.0.1:5173"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True


settings = Settings()


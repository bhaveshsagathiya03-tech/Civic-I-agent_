from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "CIVIC-I API"
    app_env: str = "development"
    secret_key: str = "change-this-development-secret-before-deployment"
    database_url: str = "sqlite:///./civic_i.db"
    media_dir: str = "./media"
    max_upload_mb: int = 10
    admin_email: str | None = None
    admin_password: str | None = None
    jwt_expiry_minutes: int = 720
    yolo_weights: str | None = None
    yolo_confidence: float = 0.35
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    duplicate_radius_m: float = 40.0
    duplicate_window_days: int = 30
    model_name: str = "CIVIC-I two-class detector"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def media_path(self) -> Path:
        path = Path(self.media_dir)
        return path if path.is_absolute() else (BASE_DIR / path).resolve()

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.allowed_origins.split(",") if x.strip()]

settings = Settings()

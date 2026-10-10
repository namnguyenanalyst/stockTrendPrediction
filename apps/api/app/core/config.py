"""Cấu hình ứng dụng Backend API sử dụng Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình tập trung cho VN Stock FastAPI Backend."""

    PROJECT_NAME: str = "VN Stock Prediction API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Backend RESTful API phục vụ truy vấn dữ liệu chứng khoán, dự báo xu hướng AI và kiểm thử chiến lược đầu tư."
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["*"]

    # Đường dẫn liên kết sang tầng ML engine
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MONOREPO_ROOT: Path = BASE_DIR.parent.parent
    ML_APP_DIR: Path = MONOREPO_ROOT / "apps" / "ml"
    DATA_DIR: Path = ML_APP_DIR / "data"
    MODELS_DIR: Path = ML_APP_DIR / "models"

    # Danh mục mã cổ phiếu hỗ trợ
    CORE_SYMBOLS: list[str] = ["VIC", "HPG", "FPT", "VNM", "MWG"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

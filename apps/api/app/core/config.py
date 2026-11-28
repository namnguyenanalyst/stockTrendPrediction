"""Cấu hình ứng dụng Backend API sử dụng Pydantic Settings."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình tập trung cho VN Stock FastAPI Backend."""

    PROJECT_NAME: str = "VN Stock Prediction API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Backend RESTful API phục vụ truy vấn dữ liệu chứng khoán, dự báo xu hướng AI và kiểm thử chiến lược đầu tư."
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Đường dẫn liên kết sang tầng ML engine
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MONOREPO_ROOT: Path = BASE_DIR.parent.parent
    ML_APP_DIR: Path = MONOREPO_ROOT / "apps" / "ml"
    DATA_DIR: Path = ML_APP_DIR / "data"
    MODELS_DIR: Path = ML_APP_DIR / "models"

    # Danh mục mã cổ phiếu và chỉ số hỗ trợ
    # CORE_SYMBOLS: Tập 5 cổ phiếu đại diện trọng số cao thuộc 5 ngành cốt lõi của VN30
    # (VIC: Bất động sản, HPG: Thép/Vật liệu, FPT: Công nghệ, VNM: Tiêu dùng thiết yếu, MWG: Bán lẻ).
    # Dùng cho benchmark đối sánh, kiểm thử hồi quy nhanh và batch prediction mức rút gọn (scope="CORE").
    CORE_SYMBOLS: list[str] = ["VIC", "HPG", "FPT", "VNM", "MWG"]
    VN30_SYMBOLS: list[str] = [
        "ACB",
        "BCM",
        "BID",
        "BVH",
        "CTG",
        "FPT",
        "GAS",
        "GVR",
        "HDB",
        "HPG",
        "MBB",
        "MSN",
        "MWG",
        "PLX",
        "POW",
        "SAB",
        "SHB",
        "SSB",
        "SSI",
        "STB",
        "TCB",
        "TPB",
        "VCB",
        "VHM",
        "VIB",
        "VIC",
        "VJC",
        "VNM",
        "VPB",
        "VRE",
    ]
    SUPPORTED_INDICES: list[str] = ["VNINDEX", "VN30"]
    AUTO_SYNC_ON_STARTUP: bool = True

    # Cấu hình CSDL PostgreSQL & Connection Pool
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "vn_stock"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None
    ASYNC_DATABASE_URL: str | None = None
    SYNC_DATABASE_URL: str | None = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # Cấu hình Bảo mật & JWT Authentication
    JWT_SECRET_KEY: str = "super_secret_jwt_key_must_be_changed_in_prod_32chars"
    SOLE_ADMIN_EMAIL: str = "admin@vnstock"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    FRONTEND_PUBLIC_URL: str = "http://localhost:3000"

    @model_validator(mode="after")
    def validate_frontend_url(self):
        from urllib.parse import urlsplit
        url = urlsplit(self.FRONTEND_PUBLIC_URL)
        if url.scheme not in ("http", "https") or not url.netloc or url.query or url.fragment or url.username:
            raise ValueError("FRONTEND_PUBLIC_URL must be a trusted HTTP(S) URL")
        if self.ENVIRONMENT.lower() == "production" and url.scheme != "https":
            raise ValueError("Production FRONTEND_PUBLIC_URL requires HTTPS")
        return self

    # Khóa bí mật phục vụ quy trình retrain tự trị nội bộ (Gói 2/3)
    INTERNAL_WORKER_SECRET: str | None = None

    @model_validator(mode="after")
    def validate_production_secret(self):
        if self.ENVIRONMENT.lower() == "production" and (
            self.JWT_SECRET_KEY == type(self).model_fields["JWT_SECRET_KEY"].default
            or len(self.JWT_SECRET_KEY.encode()) < 32
        ):
            raise ValueError("Production requires a dedicated JWT_SECRET_KEY of at least 32 bytes")
        return self

    @property
    def async_db_url(self) -> str:
        """Đường dẫn kết nối CSDL bất đồng bộ (cho SQLAlchemy AsyncEngine / asyncpg)."""
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_db_url(self) -> str:
        """Đường dẫn kết nối CSDL đồng bộ (cho Alembic migrations / psycopg)."""
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql+asyncpg://"):
                return url.replace("postgresql+asyncpg://", "postgresql://", 1)
            return url
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[4] / ".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://mercor:mercor123@localhost:5432/mercor_time_tracker"
    )
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # File uploads
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    max_screenshot_size: int = int(os.getenv("MAX_SCREENSHOT_SIZE", "5242880"))  # 5MB
    
    # Screenshot settings
    screenshot_compression_quality: int = 85
    allowed_screenshot_formats: list = ["jpg", "jpeg", "png"]
    
    # API settings
    api_v1_prefix: str = "/api/v1"

    # SMTP / Email
    smtp_host: Optional[str] = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    from_email: Optional[str] = os.getenv("FROM_EMAIL")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
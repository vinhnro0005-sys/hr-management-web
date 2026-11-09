from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Định vị thư mục gốc hr_management để nạp file .env chính xác
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "hr_management"
    session_secret_key: str

    # Cấu hình SMTP gửi email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    emails_from_email: str = ""
    emails_from_name: str = "Phòng Nhân Sự HR"

    model_config = SettingsConfigDict(
        env_file=(str(ENV_FILE), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    CHROMA_PERSIST_DIR: str = "./chroma_policy_db"


settings = Settings()

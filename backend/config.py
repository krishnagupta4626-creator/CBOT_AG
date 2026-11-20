import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")

    # MySQL Configuration
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "emopal_db")

    # FastAPI Server
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "127.0.0.1")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Storage paths
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "knowledge_base"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    AUDIO_DIR: Path = BASE_DIR / "audio_cache"

    @property
    def mysql_url(self) -> str:
        # PyMySQL connection URL
        pwd = f":{self.MYSQL_PASSWORD}" if self.MYSQL_PASSWORD else ""
        return f"mysql+pymysql://{self.MYSQL_USER}{pwd}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    @property
    def sqlite_fallback_url(self) -> str:
        # Fallback local SQLite database for graceful resilience if MySQL is offline
        db_path = BASE_DIR / "emopal_fallback.db"
        return f"sqlite:///{db_path}"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

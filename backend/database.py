import logging
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.config import settings
from backend.models import Base

logger = logging.getLogger("emopal.database")

def create_db_engine():
    """
    Initializes database engine. First tries MySQL. If MySQL is unavailable
    (e.g., password not yet configured or service offline), falls back to SQLite
    so the system remains functional while alerting the developer.
    """
    # 1. Try MySQL
    try:
        # Check / create MySQL database if needed
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset="utf8mb4"
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()

        engine = create_engine(
            settings.mysql_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        # Test connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info(f"Connected to MySQL database '{settings.MYSQL_DATABASE}' successfully.")
        return engine, "mysql"
    except Exception as e:
        logger.warning(
            f"MySQL connection to {settings.MYSQL_HOST}:{settings.MYSQL_PORT} failed ({e}). "
            f"Falling back to local SQLite database: {settings.sqlite_fallback_url}. "
            f"Update your .env with valid MYSQL_PASSWORD to switch back to MySQL."
        )

    # 2. Fallback to SQLite
    engine = create_engine(
        settings.sqlite_fallback_url,
        connect_args={"check_same_thread": False},
        echo=False
    )
    return engine, "sqlite"

engine, DB_ENGINE_TYPE = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables in the active database engine."""
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database tables initialized on {DB_ENGINE_TYPE.upper()}.")

def get_db():
    """FastAPI dependency for database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

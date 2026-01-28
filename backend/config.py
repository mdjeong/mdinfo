"""
MDinfo 백엔드 설정 관리 모듈

모든 설정값을 중앙에서 관리하고 환경 변수로 오버라이드 가능하게 합니다.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv()

# 경로 설정
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
SOURCES_FILE = BACKEND_DIR / "sources.json"


class Settings:
    """애플리케이션 설정"""

    # Database
    # SQLite: sqlite:///./mdinfo.db
    # PostgreSQL: postgresql://user:password@localhost:5432/mdinfo
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mdinfo.db")

    # PostgreSQL 개별 설정 (DATABASE_URL이 없을 때 사용)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "mdinfo")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "mdinfo")

    @classmethod
    def get_database_url(cls) -> str:
        """DATABASE_URL 반환. 환경 변수가 없으면 PostgreSQL 개별 설정 사용."""
        url = os.getenv("DATABASE_URL")
        if url:
            return url

        # PostgreSQL 개별 설정이 있으면 URL 생성
        if cls.POSTGRES_PASSWORD:
            return (
                f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
                f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
            )

        # 기본값: SQLite
        return "sqlite:///./mdinfo.db"

    # API Server
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")

    # CORS 설정
    CORS_ALLOW_CREDENTIALS: bool = (
        os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"
    )
    CORS_ALLOW_METHODS: List[str] = os.getenv("CORS_ALLOW_METHODS", "GET").split(",")
    CORS_ALLOW_HEADERS: List[str] = os.getenv(
        "CORS_ALLOW_HEADERS", "Content-Type,Authorization"
    ).split(",")
    CORS_MAX_AGE: int = int(os.getenv("CORS_MAX_AGE", "600"))

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    OPENAI_TEXT_LIMIT: int = int(os.getenv("OPENAI_TEXT_LIMIT", "4000"))

    # Collection
    MAX_SUMMARY_WORKERS: int = int(os.getenv("MAX_SUMMARY_WORKERS", "5"))
    SCHOLAR_TIMEOUT: int = int(os.getenv("SCHOLAR_TIMEOUT", "60"))
    RSS_FETCH_TIMEOUT: int = int(os.getenv("RSS_FETCH_TIMEOUT", "10"))

    # Limits
    TITLE_MAX_LENGTH: int = int(os.getenv("TITLE_MAX_LENGTH", "500"))
    SUMMARY_MAX_LENGTH: int = int(os.getenv("SUMMARY_MAX_LENGTH", "10000"))
    SOURCE_MAX_LENGTH: int = int(os.getenv("SOURCE_MAX_LENGTH", "255"))

    # PubMed
    PUBMED_EMAIL: str = os.getenv("PUBMED_EMAIL", "")

    # Scheduler
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
    SCHEDULER_COLLECTION_HOURS: str = os.getenv("SCHEDULER_COLLECTION_HOURS", "6,18")
    SCHEDULER_INTERVAL_HOURS: int = int(os.getenv("SCHEDULER_INTERVAL_HOURS", "0"))

    @classmethod
    def validate_required(cls, *keys: str) -> None:
        """필수 환경 변수 검증. 누락 시 예외 발생."""
        missing = []
        for key in keys:
            value = getattr(cls, key, None)
            if not value:
                missing.append(key)
        if missing:
            raise EnvironmentError(
                f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing)}\n"
                f".env 파일을 확인하거나 환경 변수를 설정해주세요."
            )

    @classmethod
    def validate_for_collection(cls) -> None:
        """데이터 수집에 필요한 환경 변수 검증"""
        cls.validate_required("OPENAI_API_KEY")

    @classmethod
    def validate_for_api(cls) -> None:
        """API 서버 실행에 필요한 환경 변수 검증 (현재는 필수 없음)"""
        pass


settings = Settings()

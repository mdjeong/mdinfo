# 백엔드 개선사항 문서

> 최종 업데이트: 2026-01-28
> 상태: 진행 중

이 문서는 MDinfo 백엔드 코드 진단 결과 발견된 개선사항을 정리합니다.

---

## 목차

1. [개선사항 체크리스트](#개선사항-체크리스트)
2. [Critical - 즉시 해결](#1-critical---즉시-해결)
3. [High - 높은 우선순위](#2-high---높은-우선순위)
4. [Medium - 중간 우선순위](#3-medium---중간-우선순위)
5. [Low - 낮은 우선순위](#4-low---낮은-우선순위)

---

## 개선사항 체크리스트

### Critical (즉시 해결)
- [x] C1. API 키 필수 검증 추가
- [x] C2. 에러 응답 형식 표준화
- [x] C3. `get_db()` 함수 중복 제거
- [x] C4. 설정값을 환경 변수로 이동

### High (높은 우선순위)
- [x] H1. 페이지네이션 메타데이터 추가
- [x] H2. RSS/PubMed/Scholar 병렬 수집
- [x] H3. 모든 외부 API에 재시도 로직 적용
- [x] H4. 타입 힌트 보강

### Medium (중간 우선순위)
- [x] M1. API 응답 캐싱 전략 도입
- [x] M2. 필터링 및 검색 기능 추가
- [x] M3. 수집 파이프라인 상태 추적
- [x] M4. 중복 확인 로직 최적화

### Low (낮은 우선순위)
- [x] L1. PostgreSQL 지원 추가
- [x] L2. 스케줄링 기능 (APScheduler)
- [x] L3. 코드 스타일 통일 (Linting)
- [x] L4. CORS 설정 강화

---

## 1. Critical - 즉시 해결

### C1. API 키 필수 검증 추가

**현재 상태**: `summarizer.py`에서 API 키가 없으면 경고만 출력하고 계속 진행

**문제 위치**: `backend/processor/summarizer.py:14-20`

```python
# 현재 코드
api_key = api_key or os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY 미설정. 요약 기능 비활성화.")
    self.client = None
```

**개선 방안**:
```python
# config.py에 환경 변수 검증 함수 추가
def validate_env_vars():
    required = ["OPENAI_API_KEY"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"필수 환경 변수 누락: {', '.join(missing)}")

# collect_data.py 시작 시 호출
validate_env_vars()
```

**영향 범위**: `summarizer.py`, `collect_data.py`, 새 파일 `config.py`

---

### C2. 에러 응답 형식 표준화

**현재 상태**: API 에러 발생 시 표준화된 응답 형식 없음

**문제 위치**: `backend/main.py`

**개선 방안**:
```python
# schemas.py에 표준 응답 모델 추가
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    message: Optional[str] = None

# main.py에 전역 예외 핸들러 추가
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            success=False,
            error="Internal Server Error",
            message=str(exc) if DEBUG else None
        ).dict()
    )
```

**영향 범위**: `main.py`, 새 파일 `schemas.py`

---

### C3. `get_db()` 함수 중복 제거

**현재 상태**: 동일한 `get_db()` 함수가 두 파일에 정의됨

**문제 위치**:
- `backend/database.py:13-18`
- `backend/main.py:31-36`

**개선 방안**:
```python
# main.py에서 database.py의 get_db를 import하여 사용
from database import get_db

# main.py의 중복 get_db() 함수 삭제
```

**영향 범위**: `main.py`

---

### C4. 설정값을 환경 변수로 이동

**현재 상태**: 매직 넘버가 코드 곳곳에 하드코딩됨

**문제 위치**:
| 파일 | 라인 | 값 | 설명 |
|------|------|-----|------|
| `collect_data.py` | 26 | 5 | MAX_SUMMARY_WORKERS |
| `collect_data.py` | 27 | 60 | SCHOLAR_COLLECTION_TIMEOUT |
| `rss_collector.py` | 85 | 500 | TITLE_MAX_LENGTH |
| `rss_collector.py` | 87 | 10000 | SUMMARY_MAX_LENGTH |
| `summarizer.py` | 33 | 4000 | TEXT_TRUNCATE_LENGTH |
| `summarizer.py` | 48 | 1000 | MAX_TOKENS |
| `database.py` | 4 | - | DATABASE_URL |

**개선 방안**:
```python
# backend/config.py 생성
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./mdinfo.db"

    # API
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEXT_LIMIT: int = 4000

    # Collection
    MAX_SUMMARY_WORKERS: int = 5
    SCHOLAR_TIMEOUT: int = 60
    RSS_FETCH_TIMEOUT: int = 10

    # Limits
    TITLE_MAX_LENGTH: int = 500
    SUMMARY_MAX_LENGTH: int = 10000
    SOURCE_MAX_LENGTH: int = 255

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

**영향 범위**: 모든 백엔드 파일, 새 파일 `config.py`

---

## 2. High - 높은 우선순위

### H1. 페이지네이션 메타데이터 추가

**현재 상태**: API 응답에 전체 개수, 다음 페이지 여부 정보 없음

**문제 위치**: `backend/main.py:42-49`, `backend/crud.py:38-39`

**개선 방안**:
```python
# schemas.py
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool

# crud.py
def get_articles_count(db: Session) -> int:
    return db.query(models.Article).count()

# main.py
@app.get("/articles/", response_model=PaginatedResponse[ArticleResponse])
def read_articles(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    total = crud.get_articles_count(db)
    articles = crud.get_articles(db, skip=skip, limit=limit)
    return PaginatedResponse(
        items=articles,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )
```

**영향 범위**: `main.py`, `crud.py`, `schemas.py`, 프론트엔드 `types.ts`

---

### H2. RSS/PubMed/Scholar 병렬 수집

**현재 상태**: 각 수집기가 순차적으로 실행됨

**문제 위치**: `backend/collect_data.py:70-104`

**개선 방안**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_collection():
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(RSSCollector().fetch_feeds): 'rss',
            executor.submit(PubMedCollector().search_articles, 3): 'pubmed',
            executor.submit(GoogleScholarCollector().search_articles, 3): 'scholar',
        }

        results = {'rss': [], 'pubmed': [], 'scholar': []}
        for future in as_completed(futures, timeout=120):
            source = futures[future]
            try:
                results[source] = future.result()
            except Exception as e:
                logger.error(f"{source} 수집 실패: {e}")

        return results
```

**영향 범위**: `collect_data.py`

---

### H3. 모든 외부 API에 재시도 로직 적용

**현재 상태**: RSS만 `@retry` 데코레이터 적용

**문제 위치**:
- `backend/collector/rss_collector.py:42-46` (적용됨)
- `backend/collector/pubmed_collector.py` (미적용)
- `backend/collector/scholar_collector.py` (미적용)
- `backend/processor/summarizer.py` (미적용)

**개선 방안**:
```python
# backend/utils/retry.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

RETRY_CONFIG = {
    'stop': stop_after_attempt(3),
    'wait': wait_exponential(multiplier=1, min=2, max=10),
    'retry': retry_if_exception_type((
        requests.RequestException,
        requests.Timeout,
        ConnectionError,
    ))
}

@retry(**RETRY_CONFIG)
def fetch_with_retry(url: str, timeout: int = 10, **kwargs) -> requests.Response:
    response = requests.get(url, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response

# OpenAI용 재시도
from openai import RateLimitError, APIError

OPENAI_RETRY_CONFIG = {
    'stop': stop_after_attempt(3),
    'wait': wait_exponential(multiplier=2, min=4, max=30),
    'retry': retry_if_exception_type((RateLimitError, APIError))
}
```

**영향 범위**: `rss_collector.py`, `pubmed_collector.py`, `scholar_collector.py`, `summarizer.py`, 새 파일 `utils/retry.py`

---

### H4. 타입 힌트 보강

**현재 상태**: 반환 타입이 `dict`로만 명시되거나 누락됨

**문제 위치**:
- `backend/processor/summarizer.py:22` - `def summarize(...) -> dict`
- `backend/collector/rss_collector.py` - 반환 타입 누락
- `backend/collector/pubmed_collector.py` - 반환 타입 누락

**개선 방안**:
```python
# backend/types.py
from typing import TypedDict, Optional, List

class ArticleDict(TypedDict):
    title: str
    link: str
    source: str
    text: Optional[str]
    published_date: Optional[str]

class SummaryResult(TypedDict):
    title_ko: Optional[str]
    summary: Optional[str]

# summarizer.py
def summarize(self, title: str, text: str, context: str = "dermatology research") -> SummaryResult:
    ...

# rss_collector.py
def fetch_feeds(self) -> List[ArticleDict]:
    ...
```

**영향 범위**: `summarizer.py`, `rss_collector.py`, `pubmed_collector.py`, `scholar_collector.py`, 새 파일 `types.py`

---

## 3. Medium - 중간 우선순위

### M1. API 응답 캐싱 전략 도입

**현재 상태**: 동일 요청에도 매번 DB 쿼리 실행

**문제 위치**: `backend/main.py`, `backend/crud.py`

**개선 방안**:
```python
# requirements.txt에 추가
# fastapi-cache2[inmemory]

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())

@app.get("/articles/")
@cache(expire=300)  # 5분 캐시
def read_articles(...):
    ...
```

**영향 범위**: `main.py`, `requirements.txt`

---

### M2. 필터링 및 검색 기능 추가

**현재 상태**: 전체 목록 조회만 가능

**문제 위치**: `backend/main.py:42-49`

**개선 방안**:
```python
@app.get("/articles/")
def read_articles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    source: Optional[str] = Query(None, description="소스별 필터링"),
    search: Optional[str] = Query(None, description="제목/요약 검색"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Article)

    if source:
        query = query.filter(models.Article.source == source)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.Article.title.ilike(search_term)) |
            (models.Article.title_ko.ilike(search_term)) |
            (models.Article.summary.ilike(search_term))
        )

    total = query.count()
    articles = query.order_by(models.Article.published_date.desc())\
        .offset(skip).limit(limit).all()

    return PaginatedResponse(items=articles, total=total, ...)
```

**영향 범위**: `main.py`, `crud.py`

---

### M3. 수집 파이프라인 상태 추적

**현재 상태**: 수집/요약 단계별 성공/실패 통계 없음

**문제 위치**: `backend/collect_data.py`

**개선 방안**:
```python
# backend/types.py
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime

@dataclass
class CollectionStats:
    stage: str
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[Dict] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return 0

@dataclass
class PipelineReport:
    rss: CollectionStats
    pubmed: CollectionStats
    scholar: CollectionStats
    summarize: CollectionStats
    save: CollectionStats

    def to_dict(self) -> Dict:
        return {
            'rss': asdict(self.rss),
            'pubmed': asdict(self.pubmed),
            # ...
        }
```

**영향 범위**: `collect_data.py`, `types.py`

---

### M4. 중복 확인 로직 최적화

**현재 상태**: 아이템당 개별 DB 쿼리 (N번)

**문제 위치**: `backend/collect_data.py:64, 74, 98`

**개선 방안**:
```python
# crud.py
def get_existing_urls(db: Session, urls: List[str]) -> Set[str]:
    """한 번의 쿼리로 존재하는 URL 집합 반환"""
    if not urls:
        return set()

    existing = db.query(models.Article.url).filter(
        models.Article.url.in_(urls)
    ).all()
    return {row[0] for row in existing}

# collect_data.py
def filter_new_items(db: Session, items: List[Dict]) -> List[Dict]:
    """중복 제거된 새 아이템만 반환"""
    if not items:
        return []

    urls = [item['link'] for item in items]
    existing_urls = crud.get_existing_urls(db, urls)

    # 수집된 아이템 내 중복도 제거
    seen = set()
    new_items = []
    for item in items:
        if item['link'] not in existing_urls and item['link'] not in seen:
            seen.add(item['link'])
            new_items.append(item)

    return new_items
```

**영향 범위**: `crud.py`, `collect_data.py`

---

## 4. Low - 낮은 우선순위

### L1. PostgreSQL 지원 추가

**현재 상태**: SQLite만 지원

**문제 위치**: `backend/database.py:4`

**개선 방안**:
```python
# config.py
class Settings(BaseSettings):
    DATABASE_TYPE: str = "sqlite"  # sqlite | postgresql

    # SQLite
    SQLITE_PATH: str = "./mdinfo.db"

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "mdinfo"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "mdinfo"

    @property
    def database_url(self) -> str:
        if self.DATABASE_TYPE == "postgresql":
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return f"sqlite:///{self.SQLITE_PATH}"

# database.py
from config import settings
SQLALCHEMY_DATABASE_URL = settings.database_url
```

**영향 범위**: `database.py`, `config.py`, `requirements.txt` (psycopg2)

---

### L2. 스케줄링 기능 (APScheduler)

**현재 상태**: 수동 실행만 가능

**문제 위치**: `backend/collect_data.py`

**개선 방안**:
```python
# backend/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

def setup_scheduler():
    # 매일 오전 6시, 오후 6시 수집
    scheduler.add_job(
        run_collection,
        trigger=CronTrigger(hour='6,18'),
        id='daily_collection',
        replace_existing=True
    )

    scheduler.start()
    logger.info("스케줄러 시작됨")

# main.py
from scheduler import setup_scheduler

@app.on_event("startup")
def startup_event():
    setup_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
```

**영향 범위**: 새 파일 `scheduler.py`, `main.py`, `requirements.txt`

---

### L3. 코드 스타일 통일 (Linting)

**현재 상태**: 일관되지 않은 코드 스타일

**개선 방안**:
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["collector", "processor"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

```bash
# 실행
ruff check backend/
ruff format backend/
mypy backend/
```

**영향 범위**: 새 파일 `pyproject.toml`, 모든 Python 파일

---

### L4. CORS 설정 강화

**현재 상태**: `allow_credentials=True` 설정됨

**문제 위치**: `backend/main.py:21-29`

**개선 방안**:
```python
# config.py
class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_MAX_AGE: int = 600

# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=settings.CORS_MAX_AGE,
)
```

**영향 범위**: `main.py`, `config.py`

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-28 | 최초 문서 작성 |
| 2026-01-28 | Critical 항목 (C1-C4) 구현 완료 |
| 2026-01-28 | H2. 병렬 수집 구현 완료 |
| 2026-01-28 | High 항목 (H1-H4) 구현 완료 |
| 2026-01-28 | Medium 항목 (M1-M4) 구현 완료 |
| 2026-01-28 | Low 항목 (L1-L4) 구현 완료 - 전체 완료 |

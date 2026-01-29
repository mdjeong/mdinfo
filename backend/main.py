import logging
from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import crud, models, database
from .config import settings
from .database import get_db
from .schemas import ArticleResponse, ApiResponse, PaginatedResponse
from .utils.cache import get_cache, invalidate_cache
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MDinfo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    max_age=settings.CORS_MAX_AGE,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러 - 표준화된 에러 응답 반환"""
    logger.error(f"Unhandled exception: {type(exc).__name__}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            success=False,
            error="Internal Server Error",
            message="서버 내부 오류가 발생했습니다.",
        ).model_dump(),
    )

@app.get("/")
def read_root():
    return {"message": "Derma-Insight Backend is running!"}

@app.get("/articles/", response_model=PaginatedResponse[ArticleResponse])
def read_articles(
    skip: int = Query(default=0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(default=20, ge=1, le=100, description="반환할 최대 항목 수"),
    category: Optional[str] = Query(default=None, description="카테고리 필터링 ('news', 'paper', 'all')"),
    source: Optional[str] = Query(default=None, description="소스별 필터링"),
    search: Optional[str] = Query(default=None, description="제목/요약 검색"),
    db: Session = Depends(get_db),
):
    """아티클 목록 조회 (페이지네이션, 카테고리, 필터링, 검색 지원)"""
    cache = get_cache()
    cache_key = f"articles:{skip}:{limit}:{category}:{source}:{search}"

    # 캐시 조회
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # DB 조회
    total, articles = crud.get_articles_filtered(
        db, skip=skip, limit=limit, category=category, source=source, search=search
    )

    result = PaginatedResponse(
        items=articles,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )

    # 캐시 저장 (5분)
    cache.set(cache_key, result, ttl=300)
    return result

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "healthy"}


@app.get("/scheduler/status")
def scheduler_status():
    """스케줄러 상태 조회"""
    from .scheduler import get_scheduler_status

    return get_scheduler_status()


@app.on_event("startup")
def startup_event():
    """앱 시작 시 스케줄러 초기화"""
    if settings.SCHEDULER_ENABLED:
        from .scheduler import setup_scheduler

        interval = settings.SCHEDULER_INTERVAL_HOURS or None
        setup_scheduler(
            collection_hours=settings.SCHEDULER_COLLECTION_HOURS,
            collection_interval_hours=interval,
        )
        logger.info("스케줄러 활성화됨")


@app.on_event("shutdown")
def shutdown_event():
    """앱 종료 시 스케줄러 정리"""
    from .scheduler import shutdown_scheduler

    shutdown_scheduler()

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models
from datetime import datetime

logger = logging.getLogger(__name__)


def get_article_by_url(db: Session, url: str) -> Optional[models.Article]:
    """URL로 아티클 조회"""
    return db.query(models.Article).filter(models.Article.url == url).first()

def create_article(db: Session, article_data: dict) -> Optional[models.Article]:
    try:
        db_article = models.Article(
            title=article_data.get("title"),
            title_ko=article_data.get("title_ko"),
            url=article_data.get("link"),
            source=article_data.get("source"),
            published_date=article_data.get("published"),
            summary=article_data.get("summary"),
            original_abstract=article_data.get("original_abstract", ""),
            keywords=article_data.get("keywords", ""),
            created_at=datetime.now()
        )
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return db_article
    except IntegrityError:
        db.rollback()
        logger.warning(f"중복 아티클: {article_data.get('title')}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"DB 저장 실패: {e}", exc_info=True)
        raise

def get_articles(db: Session, skip: int = 0, limit: int = 100) -> List[models.Article]:
    """아티클 목록 조회 (페이지네이션)"""
    return db.query(models.Article).order_by(models.Article.published_date.desc()).offset(skip).limit(limit).all()


def get_articles_count(db: Session) -> int:
    """전체 아티클 개수 반환"""
    return db.query(models.Article).count()


def get_existing_urls(db: Session, urls: List[str]) -> set:
    """URL 목록 중 이미 존재하는 URL 집합 반환 (배치 조회)

    Args:
        db: DB 세션
        urls: 확인할 URL 목록

    Returns:
        이미 존재하는 URL 집합
    """
    if not urls:
        return set()

    existing = db.query(models.Article.url).filter(
        models.Article.url.in_(urls)
    ).all()
    return {row[0] for row in existing}


def get_articles_filtered(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    search: Optional[str] = None,
) -> tuple[int, List[models.Article]]:
    """필터링/검색을 지원하는 아티클 목록 조회

    Args:
        db: DB 세션
        skip: 건너뛸 항목 수
        limit: 반환할 최대 항목 수
        source: 소스별 필터링 (부분 일치)
        search: 제목/요약 검색어

    Returns:
        (전체 개수, 아티클 목록) 튜플
    """
    query = db.query(models.Article)

    # 소스 필터링
    if source:
        query = query.filter(models.Article.source.ilike(f"%{source}%"))

    # 검색어 필터링 (제목, 한글 제목, 요약에서 검색)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.Article.title.ilike(search_term))
            | (models.Article.title_ko.ilike(search_term))
            | (models.Article.summary.ilike(search_term))
        )

    # 전체 개수 (필터 적용 후)
    total = query.count()

    # 정렬 및 페이지네이션
    articles = (
        query.order_by(models.Article.published_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return total, articles

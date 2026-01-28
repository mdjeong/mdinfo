import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models
from datetime import datetime

logger = logging.getLogger(__name__)

def get_article_by_url(db: Session, url: str):
    return db.query(models.Article).filter(models.Article.url == url).first()

def create_article(db: Session, article_data: dict):
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

def get_articles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Article).order_by(models.Article.published_date.desc()).offset(skip).limit(limit).all()

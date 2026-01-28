import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from backend.database import SessionLocal, engine, Base
from backend.collector.rss_collector import RSSCollector
from backend.collector.pubmed_collector import PubMedCollector
from backend.collector.scholar_collector import GoogleScholarCollector
from backend.processor.summarizer import Summarizer
from backend import crud, models

# Creates tables if they don't exist
Base.metadata.create_all(bind=engine)

def run_collection():
    db = SessionLocal()
    summarizer = Summarizer()

    try:
        # 1. RSS Collection
        logger.info("RSS 수집 시작...")
        rss_collector = RSSCollector()
        rss_results = rss_collector.fetch_feeds()
        for item in rss_results:
            if not crud.get_article_by_url(db, item['link']):
                logger.info(f"새 RSS 아티클: {item['title']}")
                if item.get('summary'):
                    logger.info(f"요약 중: {item['title'][:30]}...")
                    ai_result = summarizer.summarize(item['title'], item['summary'])
                    item['summary'] = ai_result.get('summary', item['summary'])
                    item['title_ko'] = ai_result.get('title_ko')
                crud.create_article(db, item)

        # 2. PubMed Collection
        logger.info("PubMed 수집 시작...")
        pubmed_collector = PubMedCollector()
        pubmed_results = pubmed_collector.search_articles(max_results=3)
        for item in pubmed_results:
            if not crud.get_article_by_url(db, item['link']):
                logger.info(f"새 PubMed 아티클: {item['title']}")

                original_abstract = item['summary']
                item['original_abstract'] = original_abstract

                if original_abstract:
                    logger.info("요약 중...")
                    ai_result = summarizer.summarize(item['title'], original_abstract)
                    item['summary'] = ai_result.get('summary')
                    item['title_ko'] = ai_result.get('title_ko')
                else:
                    item['summary'] = "요약할 본문이 없습니다."

                crud.create_article(db, item)

        # 3. Google Scholar Collection
        logger.info("Google Scholar 수집 시작...")
        scholar_collector = GoogleScholarCollector()
        scholar_results = scholar_collector.search_articles(max_results=3)
        for item in scholar_results:
            if not crud.get_article_by_url(db, item['link']):
                logger.info(f"새 Scholar 아티클: {item['title']}")

                original_abstract = item['summary']
                item['original_abstract'] = original_abstract

                if original_abstract:
                    logger.info("요약 중...")
                    ai_result = summarizer.summarize(item['title'], original_abstract)
                    item['summary'] = ai_result.get('summary')
                    item['title_ko'] = ai_result.get('title_ko')
                else:
                    item['summary'] = "요약할 본문이 없습니다."

                crud.create_article(db, item)

    except Exception as e:
        logger.error(f"수집 중 오류 발생: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    run_collection()

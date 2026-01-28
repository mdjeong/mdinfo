import sys
import os
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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

MAX_SUMMARY_WORKERS = 5
SCHOLAR_COLLECTION_TIMEOUT = 60  # seconds — safety net for Scholar collection


def _summarize_item(summarizer, item):
    """단일 아티클에 대해 OpenAI 요약을 수행하고 결과를 item에 반영하여 반환한다."""
    title = item['title']
    text = item.get('original_abstract') or item.get('summary') or ''

    if not text:
        item['summary'] = "요약할 본문이 없습니다."
        return item

    try:
        logger.info(f"요약 중: {title[:50]}...")
        ai_result = summarizer.summarize(title, text)
        item['summary'] = ai_result.get('summary', item.get('summary'))
        item['title_ko'] = ai_result.get('title_ko')
    except Exception as e:
        logger.error(f"요약 실패 ({title[:30]}): {e}")
        # 요약 실패 시 원본 유지

    return item


def run_collection():
    db = SessionLocal()
    summarizer = Summarizer()

    try:
        # ── 1단계: 수집 + 중복 필터 ──────────────────────────
        new_items = []

        # 1-a. RSS Collection
        logger.info("RSS 수집 시작...")
        rss_collector = RSSCollector()
        rss_results = rss_collector.fetch_feeds()
        for item in rss_results:
            if not crud.get_article_by_url(db, item['link']):
                logger.info(f"새 RSS 아티클: {item['title']}")
                # RSS는 summary를 요약 대상으로 사용 (original_abstract 없음)
                new_items.append(item)

        # 1-b. PubMed Collection
        logger.info("PubMed 수집 시작...")
        pubmed_collector = PubMedCollector()
        pubmed_results = pubmed_collector.search_articles(max_results=3)
        for item in pubmed_results:
            if not crud.get_article_by_url(db, item['link']):
                logger.info(f"새 PubMed 아티클: {item['title']}")
                item['original_abstract'] = item['summary']
                new_items.append(item)

        # 1-c. Google Scholar Collection (daemon thread + safety timeout)
        logger.info("Google Scholar 수집 시작...")
        scholar_results_box = []  # mutable container for thread result

        def _collect_scholar():
            collector = GoogleScholarCollector()
            scholar_results_box.extend(collector.search_articles(max_results=3))

        scholar_thread = threading.Thread(target=_collect_scholar, daemon=True)
        scholar_thread.start()
        scholar_thread.join(timeout=SCHOLAR_COLLECTION_TIMEOUT)

        if scholar_thread.is_alive():
            logger.warning(
                f"Google Scholar 수집이 {SCHOLAR_COLLECTION_TIMEOUT}초 내에 완료되지 않아 건너뜁니다. "
                f"CAPTCHA 차단 가능성이 있습니다."
            )
        else:
            for item in scholar_results_box:
                if not crud.get_article_by_url(db, item['link']):
                    logger.info(f"새 Scholar 아티클: {item['title']}")
                    item['original_abstract'] = item['summary']
                    new_items.append(item)

        logger.info(f"수집 완료. 신규 아티클 {len(new_items)}건 요약 시작...")

        # ── 2단계: 병렬 요약 ─────────────────────────────────
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=MAX_SUMMARY_WORKERS) as executor:
            futures = {
                executor.submit(_summarize_item, summarizer, item): item
                for item in new_items
            }
            summarized_items = []
            for future in as_completed(futures):
                try:
                    summarized_items.append(future.result())
                except Exception as e:
                    failed_item = futures[future]
                    logger.error(f"요약 작업 예외 ({failed_item['title'][:30]}): {e}")
                    summarized_items.append(failed_item)

        elapsed = time.time() - t0
        logger.info(f"요약 완료: {len(summarized_items)}건, {elapsed:.1f}초 소요")

        # ── 3단계: 순차 DB 저장 ──────────────────────────────
        saved = 0
        for item in summarized_items:
            try:
                crud.create_article(db, item)
                saved += 1
            except Exception as e:
                logger.error(f"DB 저장 실패 ({item['title'][:30]}): {e}")

        logger.info(f"저장 완료: {saved}/{len(summarized_items)}건")

    except Exception as e:
        logger.error(f"수집 중 오류 발생: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    run_collection()

import sys
import os
import logging
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from backend.config import settings
from backend.database import SessionLocal, engine, Base
from backend.collector.rss_collector import RSSCollector
from backend.collector.pubmed_collector import PubMedCollector
from backend.collector.scholar_collector import GoogleScholarCollector
from backend.processor.summarizer import Summarizer
from backend.processor.relevance_filter import MedicalRelevanceFilter
from backend.article_types import PipelineReport, StageStats, ArticleDict
from backend import crud, models
from typing import List

# Creates tables if they don't exist
Base.metadata.create_all(bind=engine)

MAX_SUMMARY_WORKERS = settings.MAX_SUMMARY_WORKERS
SCHOLAR_COLLECTION_TIMEOUT = settings.SCHOLAR_TIMEOUT
COLLECTION_TIMEOUT = 120  # RSS/PubMed 수집 타임아웃

# 뉴스 소스 정의
NEWS_SOURCES = {
    "Dermatology Times",
    "의학신문",
    "청년의사",
    "뷰티경제",
}

def categorize_source(source_name: str, source_type: str = None) -> tuple[str, str]:
    """
    소스명과 타입에서 카테고리 결정

    Args:
        source_name: 소스 이름 (예: "PubMed | Journal of...")
        source_type: 소스 타입 (예: "RSS", "API", "Scholar")

    Returns:
        (category, source_type): ('news' or 'paper', 'RSS' or 'PubMed' or 'Scholar')
    """
    # source_type 결정
    if source_type is None:
        if source_name.startswith("PubMed |"):
            source_type = "PubMed"
        elif source_name.startswith("Google Scholar"):
            source_type = "Scholar"
        else:
            source_type = "RSS"

    # category 결정
    # 1. 뉴스 소스 체크
    for news_source in NEWS_SOURCES:
        if news_source in source_name:
            return "news", source_type

    # 2. PubMed/Scholar는 무조건 논문
    if source_name.startswith("PubMed |") or source_name.startswith("Google Scholar"):
        return "paper", source_type

    # 3. 기본값: 논문
    return "paper", source_type


def _collect_rss(relevance_filter=None):
    """RSS 피드 수집"""
    logger.info("RSS 수집 시작...")
    collector = RSSCollector(relevance_filter=relevance_filter)
    results = collector.fetch_feeds()

    # RSS 결과에 category/source_type 재분류
    for item in results:
        source_name = item.get('source', '')
        category, source_type = categorize_source(source_name, 'RSS')
        item['category'] = category
        item['source_type'] = source_type

    logger.info(f"RSS 수집 완료: {len(results)}건")
    return results


def _collect_pubmed(max_results=5):
    """PubMed 수집"""
    logger.info("PubMed 수집 시작...")
    collector = PubMedCollector()
    results = collector.search_articles(max_results=max_results)
    # PubMed 결과에 original_abstract 및 category/source_type 설정
    for item in results:
        item['original_abstract'] = item.get('summary', '')
        source_name = item.get('source', '')
        category, source_type = categorize_source(source_name, 'PubMed')
        item['category'] = category
        item['source_type'] = source_type
    logger.info(f"PubMed 수집 완료: {len(results)}건")
    return results


def _collect_scholar(max_results=4):
    """Google Scholar 수집"""
    logger.info("Google Scholar 수집 시작...")
    collector = GoogleScholarCollector()
    results = collector.search_articles(max_results=max_results)
    # Scholar 결과에 original_abstract 및 category/source_type 설정
    for item in results:
        item['original_abstract'] = item.get('summary', '')
        source_name = item.get('source', '')
        category, source_type = categorize_source(source_name, 'Scholar')
        item['category'] = category
        item['source_type'] = source_type
    logger.info(f"Google Scholar 수집 완료: {len(results)}건")
    return results


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


def _filter_new_items(db, items, source_name):
    """중복 제거 후 새 아이템만 반환 (배치 조회 최적화)"""
    if not items:
        return []

    # 한 번의 쿼리로 기존 URL 조회
    urls = [item['link'] for item in items]
    existing_urls = crud.get_existing_urls(db, urls)

    # 수집된 아이템 내 중복도 제거
    seen = set()
    new_items = []

    for item in items:
        url = item['link']
        if url in existing_urls:
            continue
        if url in seen:
            continue
        seen.add(url)
        logger.info(f"새 {source_name} 아티클: {item['title'][:50]}")
        new_items.append(item)

    return new_items


def _balance_by_ratio(items: List[ArticleDict], config: dict) -> List[ArticleDict]:
    """뉴스:학술 비율을 60:40으로 조정

    Args:
        items: 수집된 아티클 리스트
        config: collection_config 딕셔너리

    Returns:
        균형 조정된 아티클 리스트
    """
    target_news_ratio = config.get('target_news_ratio', 0.60)
    target_academic_ratio = config.get('target_academic_ratio', 0.40)

    # 카테고리별 분리 ('news' and 'paper' 사용)
    news_items = [item for item in items
                  if item.get('category') == 'news']
    academic_items = [item for item in items
                      if item.get('category') == 'paper']

    logger.info(f"균형 조정 전: News={len(news_items)}, Paper={len(academic_items)}")

    # 학술 논문은 모두 유지 (수집이 어려우므로)
    target_academic = len(academic_items)

    if target_academic > 0:
        # 학술 논문 개수를 기준으로 필요한 뉴스 개수 계산
        target_news = int(target_academic * (target_news_ratio / target_academic_ratio))
    else:
        # 학술 논문이 없으면 뉴스만 반환
        logger.warning("학술 논문이 0개입니다. 비율 조정 없이 뉴스만 반환합니다.")
        return news_items

    # 뉴스가 많으면 최신순으로 샘플링
    if len(news_items) > target_news:
        news_items.sort(key=lambda x: x.get('published') or datetime.min, reverse=True)
        news_items = news_items[:target_news]
        logger.info(f"뉴스 아티클 {target_news}개로 샘플링")

    final_count = len(news_items) + len(academic_items)
    if final_count > 0:
        actual_news_ratio = len(news_items) / final_count
        actual_academic_ratio = len(academic_items) / final_count
        logger.info(f"균형 조정 완료: News={len(news_items)} ({actual_news_ratio:.1%}), "
                   f"Paper={len(academic_items)} ({actual_academic_ratio:.1%})")

    return news_items + academic_items


def run_collection() -> PipelineReport:
    """데이터 수집 파이프라인 실행

    Returns:
        PipelineReport: 실행 결과 리포트
    """
    # 필수 환경 변수 검증
    settings.validate_for_collection()

    report = PipelineReport()
    db = SessionLocal()
    summarizer = Summarizer()

    # ── 0단계: relevance_filter 초기화 ────────────────────
    relevance_filter = None
    collection_config = {}

    try:
        sources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sources.json')
        with open(sources_path, 'r', encoding='utf-8') as f:
            sources_data = json.load(f)
            collection_config = sources_data.get('collection_config', {})

        if collection_config.get('enable_relevance_filter', True):
            relevance_filter = MedicalRelevanceFilter(
                api_key=settings.OPENAI_API_KEY,
                model=collection_config.get('relevance_filter_model', 'gpt-4o-mini')
            )
            logger.info("의료 관련성 필터 활성화")
    except Exception as e:
        logger.warning(f"Relevance filter 초기화 실패: {e}")

    try:
        # ── 1단계: 병렬 수집 ──────────────────────────────────
        logger.info("=== 병렬 수집 시작 ===")
        t0 = time.time()

        all_results = {'rss': [], 'pubmed': [], 'scholar': []}

        # PubMed/Scholar 수집 개수 설정
        pubmed_limit = collection_config.get('pubmed_per_query', 5)
        scholar_limit = collection_config.get('scholar_per_query', 4)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_collect_rss, relevance_filter): 'rss',
                executor.submit(_collect_pubmed, pubmed_limit): 'pubmed',
                executor.submit(_collect_scholar, scholar_limit): 'scholar',
            }

            for future in as_completed(futures):
                source = futures[future]
                timeout = SCHOLAR_COLLECTION_TIMEOUT if source == 'scholar' else COLLECTION_TIMEOUT
                stats = StageStats(name=source)

                try:
                    results = future.result(timeout=timeout)
                    all_results[source] = results
                    stats.total = len(results)
                    stats.success = len(results)
                except TimeoutError:
                    logger.warning(f"{source} 수집 타임아웃 ({timeout}초)")
                    stats.failed = 1
                    stats.errors.append({"type": "TimeoutError", "message": f"{timeout}초 타임아웃"})
                except Exception as e:
                    logger.error(f"{source} 수집 실패: {type(e).__name__}")
                    stats.failed = 1
                    stats.errors.append({"type": type(e).__name__, "message": str(e)})

                report.collection[source] = stats

        elapsed = time.time() - t0
        for stats in report.collection.values():
            stats.duration_seconds = elapsed / 3  # 대략적인 분배
        logger.info(f"병렬 수집 완료: {elapsed:.1f}초 소요")

        # ── 2단계: 중복 필터링 ────────────────────────────────
        new_items = []
        for source, source_name in [('rss', 'RSS'), ('pubmed', 'PubMed'), ('scholar', 'Scholar')]:
            filtered = _filter_new_items(db, all_results[source], source_name)
            skipped = len(all_results[source]) - len(filtered)
            report.collection[source].skipped = skipped
            new_items.extend(filtered)

        logger.info(f"중복 제거 후: 신규 아티클 {len(new_items)}건")

        # ── 3단계: 비율 균형 조정 ─────────────────────────────
        if collection_config.get('target_news_ratio') and len(new_items) > 0:
            new_items = _balance_by_ratio(new_items, collection_config)

        logger.info(f"균형 조정 완료. {len(new_items)}건 요약 시작...")

        # ── 4단계: 병렬 요약 ─────────────────────────────────
        t0 = time.time()
        summarize_stats = StageStats(name="summarize", total=len(new_items))

        with ThreadPoolExecutor(max_workers=MAX_SUMMARY_WORKERS) as executor:
            futures = {
                executor.submit(_summarize_item, summarizer, item): item
                for item in new_items
            }
            summarized_items = []
            for future in as_completed(futures):
                try:
                    summarized_items.append(future.result())
                    summarize_stats.success += 1
                except Exception as e:
                    failed_item = futures[future]
                    logger.error(f"요약 작업 예외 ({failed_item['title'][:30]}): {e}")
                    summarized_items.append(failed_item)
                    summarize_stats.failed += 1
                    summarize_stats.errors.append({
                        "title": failed_item['title'][:50],
                        "error": type(e).__name__,
                    })

        summarize_stats.duration_seconds = time.time() - t0
        report.summarization = summarize_stats
        logger.info(f"요약 완료: {len(summarized_items)}건, {summarize_stats.duration_seconds:.1f}초 소요")

        # ── 5단계: 순차 DB 저장 ──────────────────────────────
        t0 = time.time()
        save_stats = StageStats(name="save", total=len(summarized_items))

        for item in summarized_items:
            try:
                crud.create_article(db, item)
                save_stats.success += 1
            except Exception as e:
                logger.error(f"DB 저장 실패 ({item['title'][:30]}): {e}")
                save_stats.failed += 1
                save_stats.errors.append({
                    "title": item['title'][:50],
                    "error": type(e).__name__,
                })

        save_stats.duration_seconds = time.time() - t0
        report.saving = save_stats
        logger.info(f"저장 완료: {save_stats.success}/{save_stats.total}건")

    except Exception as e:
        logger.error(f"수집 중 오류 발생: {e}", exc_info=True)
    finally:
        db.close()
        report.ended_at = datetime.now()

    # 리포트 출력
    logger.info(f"=== 파이프라인 리포트 ===")
    logger.info(json.dumps(report.to_dict(), indent=2, ensure_ascii=False, default=str))

    return report


if __name__ == "__main__":
    run_collection()

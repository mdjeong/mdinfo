from pymed import PubMed
import json
import os
import time
import logging
import sys
from typing import List, Dict
import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from article_types import ArticleDict

logger = logging.getLogger(__name__)


class PubMedCollector:
    def __init__(self, email: str = None, sources_file: str = "sources.json"):
        email = email or settings.PUBMED_EMAIL
        if not email or email == "your_email@example.com":
            logger.warning("PUBMED_EMAIL 환경 변수를 설정해주세요. 기본값을 사용합니다.")
            email = "dermainsight@example.com"
        self.pubmed = PubMed(tool="DermaInsight", email=email)
        self.queries = []
        self._load_sources(sources_file)

    def _load_sources(self, filename: str):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.queries = data.get('pubmed_queries', [])
        except Exception as e:
            logger.error(f"소스 파일 로드 실패 ({filename}): {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _query_single(self, query: str, max_results: int) -> List[ArticleDict]:
        """단일 쿼리 실행 (재시도 포함)"""
        results = []
        articles = self.pubmed.query(query, max_results=max_results)
        for article in articles:
            title = article.title
            abstract = getattr(article, 'abstract', '')
            pub_date = article.publication_date
            doi = article.doi if article.doi else ""
            journal = getattr(article, 'journal', 'Unknown Journal')

            pubmed_id = article.pubmed_id.split()[0] if article.pubmed_id else ""
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/" if pubmed_id else ""

            results.append({
                "title": title,
                "link": link,
                "summary": abstract,
                "published": pub_date,
                "source": f"PubMed | {journal}",
                "source_type": "API",
                "doi": doi,
                "keywords": query
            })
        return results

    def search_articles(self, max_results: int = 5) -> List[ArticleDict]:
        all_results = []
        for query in self.queries:
            try:
                results = self._query_single(query, max_results)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"PubMed 검색 실패 (쿼리: '{query}'): {type(e).__name__}")

            time.sleep(1.0)

        return all_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = PubMedCollector()
    print(f"Loaded {len(collector.queries)} queries.")
    articles = collector.search_articles(max_results=1)
    print(f"Found {len(articles)} articles.")
    if articles:
        print(articles[0]['title'])

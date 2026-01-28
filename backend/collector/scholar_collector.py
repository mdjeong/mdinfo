import json
import os
import time
import logging
import threading
from typing import List, Dict
from datetime import datetime
from scholarly import scholarly

logger = logging.getLogger(__name__)

KEYWORD_TIMEOUT = 15  # seconds per keyword search


def _run_with_timeout(func, args=(), timeout=KEYWORD_TIMEOUT):
    """Run *func* in a daemon thread; return (result, None) or (None, TimeoutError)."""
    result = [None]
    error = [None]

    def target():
        try:
            result[0] = func(*args)
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        return None, TimeoutError(f"{func.__name__} timed out after {timeout}s")
    if error[0] is not None:
        return None, error[0]
    return result[0], None


class GoogleScholarCollector:
    def __init__(self, sources_file: str = "sources.json"):
        self.keywords = []
        self._load_sources(sources_file)

    def _load_sources(self, filename: str):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.keywords = data.get('google_scholar_keywords', [])
        except Exception as e:
            logger.error(f"소스 파일 로드 실패 ({filename}): {e}")

    def _search_keyword(self, keyword: str, max_results: int) -> List[Dict]:
        """Search a single keyword and return article dicts."""
        results = []
        search_query = scholarly.search_pubs(keyword)
        for _ in range(max_results):
            try:
                pub = next(search_query)
            except StopIteration:
                break

            bib = pub.get('bib', {})
            title = bib.get('title', '')
            abstract = bib.get('abstract', '')
            pub_year = bib.get('pub_year', '')

            # Parse publication date (scholarly only provides year)
            if pub_year:
                try:
                    published = datetime(int(pub_year), 1, 1)
                except (ValueError, TypeError):
                    published = datetime.now()
            else:
                published = datetime.now()

            # Determine URL: prefer pub_url, fall back to eprint (PDF link)
            link = (pub.get('pub_url')
                    or pub.get('eprint_url')
                    or bib.get('url', ''))

            if not link:
                continue

            results.append({
                "title": title,
                "link": link,
                "summary": abstract,
                "published": published,
                "source": "Google Scholar",
                "source_type": "Scholar",
                "keywords": keyword,
            })

        return results

    def search_articles(self, max_results: int = 3) -> List[Dict]:
        all_results = []
        for keyword in self.keywords:
            result, err = _run_with_timeout(
                self._search_keyword, args=(keyword, max_results), timeout=KEYWORD_TIMEOUT
            )

            if isinstance(err, TimeoutError):
                logger.warning(
                    f"Google Scholar 키워드 '{keyword}' 타임아웃 ({KEYWORD_TIMEOUT}초) — "
                    f"CAPTCHA 가능성. 나머지 키워드 건너뜀."
                )
                break
            elif err is not None:
                logger.error(f"Google Scholar 검색 실패 (키워드: '{keyword}'): {err}")
                continue

            if result:
                all_results.extend(result)

            # Delay between keyword searches to avoid being blocked
            time.sleep(2)

        return all_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = GoogleScholarCollector()
    print(f"Loaded {len(collector.keywords)} keywords.")
    articles = collector.search_articles(max_results=1)
    print(f"Found {len(articles)} articles.")
    if articles:
        print(articles[0]['title'])

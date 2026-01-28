import json
import os
import time
import logging
from typing import List, Dict
from datetime import datetime
from scholarly import scholarly

logger = logging.getLogger(__name__)


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

    def search_articles(self, max_results: int = 3) -> List[Dict]:
        all_results = []
        for keyword in self.keywords:
            try:
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

                    all_results.append({
                        "title": title,
                        "link": link,
                        "summary": abstract,
                        "published": published,
                        "source": "Google Scholar",
                        "source_type": "Scholar",
                        "keywords": keyword,
                    })

                # Delay between keyword searches to avoid being blocked
                time.sleep(2)
            except Exception as e:
                logger.error(f"Google Scholar 검색 실패 (키워드: '{keyword}'): {e}")

        return all_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = GoogleScholarCollector()
    print(f"Loaded {len(collector.keywords)} keywords.")
    articles = collector.search_articles(max_results=1)
    print(f"Found {len(articles)} articles.")
    if articles:
        print(articles[0]['title'])

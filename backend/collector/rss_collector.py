import feedparser
import requests
import json
import os
import re
import html
import time
import logging
import sys
from datetime import datetime, timezone
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from article_types import ArticleDict

logger = logging.getLogger(__name__)


def _fix_escaped_cdata(raw_xml: bytes) -> bytes:
    """이스케이프된 CDATA(&lt;![CDATA[...]]&gt;)를 정상 CDATA로 변환."""
    text = raw_xml.decode('utf-8', errors='replace')
    text = text.replace('&lt;![CDATA[', '<![CDATA[')
    text = text.replace(']]&gt;', ']]>')
    return text.encode('utf-8')


def _clean_text(text: str) -> str:
    """CDATA 래퍼 제거 및 HTML 엔티티 디코딩."""
    if not text:
        return text
    text = re.sub(r'<!\[CDATA\[(.*?)]]>', r'\1', text, flags=re.DOTALL)
    text = html.unescape(text)
    return text.strip()


def _parse_datetime_safe(parsed_tuple):
    try:
        if parsed_tuple:
            return datetime(*parsed_tuple[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass
    return datetime.now(timezone.utc)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_with_retry(url: str, headers: dict) -> requests.Response:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response


class RSSCollector:
    def __init__(self, sources_file: str = "sources.json", relevance_filter=None):
        self.sources = []
        self.relevance_filter = relevance_filter
        self._load_sources(sources_file)

    def _load_sources(self, filename: str):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 전체 source object 저장 (URL뿐 아니라 메타데이터 포함)
                self.sources = data.get('rss_feeds', [])
        except Exception as e:
            logger.error(f"소스 파일 로드 실패 ({filename}): {e}")

    def fetch_feeds(self) -> List[ArticleDict]:
        results = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        for source_config in self.sources:
            url = source_config['url']
            source_name = source_config['name']
            max_items = source_config.get('max_items', 50)
            should_filter = source_config.get('filter_relevance', False)
            category = source_config.get('category', 'News')

            try:
                response = _fetch_with_retry(url, headers)
                feed = feedparser.parse(_fix_escaped_cdata(response.content))

                if feed.bozo:
                    logger.warning(f"피드 파싱 오류 {url}: {feed.bozo_exception}")
                    continue

                collected_count = 0
                for entry in feed.entries:
                    # 1. max_items 체크
                    if collected_count >= max_items:
                        break

                    published = _parse_datetime_safe(
                        getattr(entry, 'published_parsed', None)
                        or getattr(entry, 'updated_parsed', None)
                    )

                    title = _clean_text(getattr(entry, 'title', ''))[:settings.TITLE_MAX_LENGTH]
                    link = getattr(entry, 'link', '')
                    summary = _clean_text(getattr(entry, 'summary', ''))[:settings.SUMMARY_MAX_LENGTH]
                    source = feed.feed.get('title', source_name)[:settings.SOURCE_MAX_LENGTH]

                    if not link:
                        continue

                    # 2. 관련성 필터 적용
                    if should_filter and self.relevance_filter:
                        is_relevant, meta = self.relevance_filter.is_medically_relevant(
                            title, summary, source_name
                        )
                        if not is_relevant:
                            logger.info(f"필터링됨 [{source_name}]: {title[:50]}...")
                            continue

                    # 3. category 필드는 collect_data.py의 categorize_source에서 결정됨
                    # 여기서는 sources.json의 category를 임시로 저장
                    results.append({
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "published": published,
                        "source": source,
                        "source_type": "RSS",
                        "category": category  # 임시 카테고리 (나중에 categorize_source로 재분류됨)
                    })
                    collected_count += 1

                logger.info(f"RSS 수집 완료 [{source_name}]: {collected_count}개")

            except Exception as e:
                logger.error(f"피드 수집 실패 {url}: {e}")

            time.sleep(1.0)

        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = RSSCollector()
    print(f"Loaded {len(collector.sources)} feeds.")
    print(collector.fetch_feeds()[:2])

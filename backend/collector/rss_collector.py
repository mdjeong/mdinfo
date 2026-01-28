import feedparser
import requests
import json
import os
import re
import html
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

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
    def __init__(self, sources_file: str = "sources.json"):
        self.sources = []
        self._load_sources(sources_file)

    def _load_sources(self, filename: str):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sources = [item['url'] for item in data.get('rss_feeds', [])]
        except Exception as e:
            logger.error(f"소스 파일 로드 실패 ({filename}): {e}")

    def fetch_feeds(self) -> List[Dict]:
        results = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        for url in self.sources:
            try:
                response = _fetch_with_retry(url, headers)
                feed = feedparser.parse(_fix_escaped_cdata(response.content))

                if feed.bozo:
                    logger.warning(f"피드 파싱 오류 {url}: {feed.bozo_exception}")
                    continue

                for entry in feed.entries:
                    published = _parse_datetime_safe(
                        getattr(entry, 'published_parsed', None)
                        or getattr(entry, 'updated_parsed', None)
                    )

                    title = _clean_text(getattr(entry, 'title', ''))[:500]
                    link = getattr(entry, 'link', '')
                    summary = _clean_text(getattr(entry, 'summary', ''))[:10000]
                    source = feed.feed.get('title', url)[:255]

                    if not link:
                        continue

                    results.append({
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "published": published,
                        "source": source,
                        "source_type": "RSS"
                    })
            except Exception as e:
                logger.error(f"피드 수집 실패 {url}: {e}")

            time.sleep(1.0)

        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = RSSCollector()
    print(f"Loaded {len(collector.sources)} feeds.")
    print(collector.fetch_feeds()[:2])

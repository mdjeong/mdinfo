# Google Scholar Collector 구현 계획

> 작성일: 2026-01-28
> 상태: 구현 전

---

## 배경

현재 데이터 수집 파이프라인은 RSS 피드와 PubMed API 두 가지 소스를 지원합니다. `sources.json`에 `google_scholar_keywords` 항목이 이미 정의되어 있고, `scholarly==1.7.11` 라이브러리도 설치되어 있으나 실제 수집기 코드는 아직 구현되지 않은 상태입니다.

---

## 목표

- Google Scholar에서 키워드 기반으로 논문을 검색하는 수집기 구현
- 기존 RSS/PubMed 수집기와 동일한 패턴 및 데이터 포맷 유지
- `collect_data.py` 파이프라인에 통합

---

## 수정 대상 파일

| 파일 | 작업 | 설명 |
|------|------|------|
| `backend/collector/scholar_collector.py` | 신규 생성 | GoogleScholarCollector 클래스 |
| `backend/collect_data.py` | 수정 | Scholar 수집 단계 추가 |

---

## 상세 설계

### 1. `backend/collector/scholar_collector.py` (신규)

기존 수집기(`RSSCollector`, `PubMedCollector`)와 동일한 클래스 구조를 따릅니다.

#### 클래스 구조

```python
class GoogleScholarCollector:
    def __init__(self, sources_file: str = "sources.json")
    def _load_sources(self, filename: str)          # sources.json에서 키워드 로드
    def search_articles(self, max_results: int = 5) -> List[Dict]  # 검색 실행
```

#### 반환 데이터 포맷

기존 수집기와 동일한 dict 키를 사용합니다:

```python
{
    "title": str,              # 논문 제목
    "link": str,               # 논문 URL (pub_url 또는 eprint)
    "summary": str,            # 초록 (abstract) 또는 snippet
    "published": datetime,     # 발행일 (연도만 제공 시 해당 연도 1월 1일)
    "source": "Google Scholar",
    "source_type": "Scholar",
    "keywords": str            # 검색에 사용된 키워드
}
```

#### `scholarly` 라이브러리 사용법

```python
from scholarly import scholarly

# 키워드 검색
search_query = scholarly.search_pubs("skin rejuvenation")

# 결과 순회 (generator)
result = next(search_query)

# 주요 필드 접근
result['bib']['title']      # 제목
result['bib']['abstract']   # 초록 (있는 경우)
result['bib']['pub_year']   # 발행 연도 (문자열)
result['pub_url']           # 논문 페이지 URL
result['eprint_url']        # PDF URL (있는 경우)
```

#### Google 차단 방지

`scholarly`는 공식 API가 아닌 웹 스크래핑 방식이므로, Google이 요청을 차단할 수 있습니다.

대응 방안:
- 키워드 간 `time.sleep(2.0)` 딜레이 적용
- 각 키워드당 `max_results`를 낮게 설정 (기본값 3~5)
- 요청 실패 시 해당 키워드를 건너뛰고 다음으로 진행

### 2. `backend/collect_data.py` 수정

기존 RSS → PubMed 수집 흐름 뒤에 Google Scholar 수집 블록을 추가합니다.

#### 추가할 코드 위치

```python
# 기존 코드
# 1. RSS Collection  (이미 존재)
# 2. PubMed Collection  (이미 존재)

# 추가
# 3. Google Scholar Collection
from backend.collector.scholar_collector import GoogleScholarCollector

print("Starting Google Scholar collection...")
scholar_collector = GoogleScholarCollector()
scholar_results = scholar_collector.search_articles(max_results=3)
for item in scholar_results:
    if not crud.get_article_by_url(db, item['link']):
        print(f"New Scholar article: {item['title']}")
        original_abstract = item['summary']
        item['original_abstract'] = original_abstract
        if original_abstract:
            print("Summarizing...")
            ai_result = summarizer.summarize(item['title'], original_abstract)
            item['summary'] = ai_result.get('summary')
            item['title_ko'] = ai_result.get('title_ko')
        else:
            item['summary'] = "요약할 본문이 없습니다."
        crud.create_article(db, item)
```

PubMed 수집과 동일한 패턴:
1. URL 중복 확인
2. 원문 초록 보존 (`original_abstract`)
3. OpenAI 요약기로 한국어 요약 생성
4. DB 저장

---

## 데이터 흐름 (수정 후)

```
RSS Feeds (feedparser) ──────┐
PubMed API (pymed) ──────────┤──→ OpenAI GPT-4o 요약기 (한국어) ──→ SQLite DB
Google Scholar (scholarly) ──┘
```

---

## 검증 방법

### 단위 테스트

```bash
cd backend
python -c "
from collector.scholar_collector import GoogleScholarCollector
c = GoogleScholarCollector()
print(f'{len(c.keywords)} keywords loaded')
results = c.search_articles(max_results=1)
print(f'{len(results)} articles found')
if results:
    print(f'Title: {results[0][\"title\"]}')
    print(f'Link: {results[0][\"link\"]}')
    print(f'Source: {results[0][\"source\"]}')
"
```

### 통합 테스트

```bash
cd backend
python collect_data.py
# 콘솔에서 "Starting Google Scholar collection..." 출력 확인
# DB에 source="Google Scholar"인 레코드 확인
```

---

## 주의 사항

- `scholarly`는 Google 웹 스크래핑 기반이므로 과도한 요청 시 IP 차단 가능
- 초기 실행 시 `max_results`를 낮게 설정하여 테스트 권장
- Google Scholar 검색 결과의 abstract가 없는 경우가 빈번하므로, snippet(짧은 발췌)으로 대체 처리 필요

---

## Implementation Plan (English Summary)

**Goal:** Implement a Google Scholar collector using the `scholarly` library, following existing collector patterns.

**Files:**
- `backend/collector/scholar_collector.py` — New file: `GoogleScholarCollector` class
- `backend/collect_data.py` — Modified: Add Scholar collection step after PubMed

**Key design decisions:**
- Same class structure as `RSSCollector`/`PubMedCollector`: `__init__`, `_load_sources`, `search_articles`
- Same return dict format: `title`, `link`, `summary`, `published`, `source`, `source_type`, `keywords`
- Rate limiting via `time.sleep(2.0)` between keyword searches to avoid Google blocking
- Graceful error handling: skip failed keywords, continue with next

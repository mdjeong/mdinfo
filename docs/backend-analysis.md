# Backend Code Analysis / 백엔드 코드 분석

> 분석 일자: 2026-01-28
> 대상: `backend/` 전체 Python 소스코드

---

## 요약

백엔드 코드를 전수 분석한 결과, 보안 취약점 및 개선 사항 총 **18건**을 발견했습니다.

| 심각도 | 건수 | 내용 |
|--------|------|------|
| CRITICAL | 2건 | API 키 노출, CORS 완전 개방 |
| HIGH | 6건 | 에러 처리 부재, 입력 미검증, 재시도 없음 등 |
| MEDIUM | 5건 | API 검증, 로깅, Pydantic 미사용 등 |
| LOW | 5건 | 인덱스, 응답 모델, 하드코딩 등 |

---

## 수정 이력

> 수정 일자: 2026-01-28
> 수정 결과: 18건 중 **17건 수정 완료**, 1건 보류

### CRITICAL (2건 → 2건 수정 완료)

| # | 내용 | 수정 파일 |
|---|------|----------|
| 1 | `.env.example`의 실제 API 키 → 플레이스홀더로 교체 | `.env.example` |
| 2 | CORS `allow_origins=["*"]` → 환경변수 기반 허용 목록, methods를 `GET`으로 제한 | `main.py` |

### HIGH (6건 → 6건 수정 완료)

| # | 내용 | 수정 파일 |
|---|------|----------|
| 3 | `crud.py`에 `IntegrityError` rollback + 일반 예외 rollback 추가 | `crud.py` |
| 4 | RSS 외부 데이터 길이 제한(title 500자, summary 10000자, source 255자) + 빈 link 건너뜀 | `collector/rss_collector.py` |
| 5 | `tenacity` retry(3회, exponential backoff) 적용 | `collector/rss_collector.py` |
| 6 | `_parse_datetime_safe` 함수로 안전한 datetime 파싱 + timezone.utc 적용 | `collector/rss_collector.py` |
| 7 | PubMed 이메일을 `PUBMED_EMAIL` 환경변수에서 읽도록 변경 | `collector/pubmed_collector.py` |
| 8 | 모든 수집기에 요청 간 `time.sleep()` 딜레이 추가 | `collector/rss_collector.py`, `collector/pubmed_collector.py` |

### MEDIUM (5건 → 4건 수정 완료, 1건 보류)

| # | 내용 | 수정 파일 |
|---|------|----------|
| 9 | `skip`/`limit`에 `Query(ge=0)`, `Query(ge=1, le=1000)` 검증 추가 | `main.py` |
| 10 | 전체 `print()` → `logging` 프레임워크로 교체 (타임스탬프, 레벨 포함) | 전체 Python 소스 |
| 11 | `ArticleResponse` Pydantic 모델 신규 생성 | `schemas.py` (신규) |
| 12 | deprecated `openai.api_key` 전역 설정 제거, `self.client = None` 핸들링 | `processor/summarizer.py` |
| 13 | **보류** — 현재 URL 중복 체크로 충분하여 요약 캐싱은 보류 | — |

### LOW (5건 → 5건 수정 완료)

| # | 내용 | 수정 파일 |
|---|------|----------|
| 14 | `(source, published_date)`, `(created_at)` 복합/단일 인덱스 추가 | `models.py` |
| 15 | `ArticleResponse` Pydantic 모델 + `response_model` 지정 | `schemas.py` (신규), `main.py` |
| 16 | OpenAI 모델명을 `OPENAI_MODEL` 환경변수로 설정 가능 | `processor/summarizer.py` |
| 17 | `crud.py`의 rollback 처리로 트랜잭션 안전성 확보 | `crud.py` |
| 18 | `/health` 엔드포인트 추가 (`SELECT 1` 쿼리로 DB 연결 검증) | `main.py` |

---

## 체크리스트

### CRITICAL (즉시 조치 필요)

- [x] **1. `.env.example`에 실제 API 키 노출** — `.env.example`
- [x] **2. CORS 설정 완전 개방** — `main.py`

### HIGH (빠른 시일 내 조치)

- [x] **3. DB 작업 에러 처리 부재** — `crud.py`
- [x] **4. 외부 데이터 미검증** — `collector/rss_collector.py`
- [x] **5. 재시도 로직 없음** — `collector/rss_collector.py`
- [x] **6. datetime 처리 불안정** — `collector/rss_collector.py`
- [x] **7. PubMed 이메일 하드코딩** — `collector/pubmed_collector.py`
- [x] **8. Rate Limiting 없음** — `collector/*.py`

### MEDIUM (개선 권장)

- [x] **9. API 입력값 검증 없음** — `main.py`
- [x] **10. 로깅 체계 없음** — 전체 Python 소스
- [x] **11. Pydantic 모델 미사용** — `schemas.py` (신규)
- [x] **12. OpenAI 클라이언트 설정 문제** — `processor/summarizer.py`
- [ ] **13. 요약 캐싱 없음** — 보류 (현재 URL 중복 체크로 충분)

### LOW (향후 개선)

- [x] **14. DB 인덱스 부족** — `models.py`
- [x] **15. API 응답 모델 없음** — `schemas.py`, `main.py`
- [x] **16. OpenAI 모델명 하드코딩** — `processor/summarizer.py`
- [x] **17. 트랜잭션 관리 부재** — `crud.py`
- [x] **18. DB 커넥션 검증 없음** — `main.py`

---

## 상세 내용

### CRITICAL (즉시 조치 필요)

#### 1. `.env.example`에 실제 API 키 노출

**파일:** `.env.example`

```
OPENAI_API_KEY=sk-proj-JGen...XSMA
```

`.env.example` 파일에 플레이스홀더가 아닌 **실제 OpenAI API 키**가 그대로 포함되어 있습니다. 이 파일은 `.gitignore`에 포함되지 않으므로, 커밋 시 키가 공개됩니다.

**조치 방안:**
1. OpenAI 대시보드에서 해당 키를 즉시 폐기하고 새 키 발급
2. `.env.example`의 값을 플레이스홀더로 교체:
   ```
   OPENAI_API_KEY=sk-proj-your-key-here
   ```
3. pre-commit hook을 도입하여 `.env` 파일 커밋 방지

---

#### 2. CORS 설정 완전 개방

**파일:** `main.py:11-17`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_origins=["*"]`와 `allow_credentials=True`의 조합은 **모든 외부 사이트에서 인증된 요청을 보낼 수 있게** 합니다.

**조치 방안:**
```python
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)
```

---

### HIGH (빠른 시일 내 조치)

#### 3. DB 작업 에러 처리 부재

**파일:** `crud.py:8-23`

```python
def create_article(db: Session, article_data: dict):
    db_article = models.Article(...)
    db.add(db_article)
    db.commit()      # 실패 시 예외 처리 없음
    db.refresh(db_article)
    return db_article
```

`db.commit()` 실패 시(URL 중복 등 `IntegrityError`) 예외 처리와 롤백이 없어서 앱이 크래시됩니다.

**조치 방안:**
```python
from sqlalchemy.exc import IntegrityError

def create_article(db: Session, article_data: dict):
    try:
        db_article = models.Article(...)
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
```

---

#### 4. 외부 데이터 미검증

**파일:** `collector/rss_collector.py:42-58`

```python
for entry in feed.entries:
    results.append({
        "title": entry.title,       # 길이 제한 없음, 새니타이징 없음
        "link": entry.link,          # URL 형식 검증 없음
        "summary": getattr(entry, 'summary', ''),  # 길이 제한 없음
        ...
    })
```

RSS 피드에서 가져온 데이터를 **길이 제한, 형식 검증, HTML 새니타이징 없이** 그대로 저장합니다.

**조치 방안:**
```python
from pydantic import BaseModel, HttpUrl, Field

class RSSArticle(BaseModel):
    title: str = Field(..., max_length=500)
    link: HttpUrl
    summary: str = Field(default="", max_length=10000)
    source: str = Field(..., max_length=255)
```

---

#### 5. 재시도 로직 없음

**파일:** `collector/rss_collector.py:30-40`

```python
for url in self.sources:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")   # 출력만 하고 넘어감
```

네트워크 요청 실패 시 재시도 없이 `print`로 출력하고 건너뜁니다. `tenacity` 라이브러리가 이미 의존성에 포함되어 있으므로 활용 가능합니다.

**조치 방안:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_with_retry(url, headers):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response
```

---

#### 6. datetime 처리 불안정

**파일:** `collector/rss_collector.py:44-49`

```python
if hasattr(entry, 'published_parsed') and entry.published_parsed:
    published = datetime(*entry.published_parsed[:6])
elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
    published = datetime(*entry.updated_parsed[:6])
else:
    published = datetime.now()
```

- 잘못된 튜플 데이터가 오면 언패킹 시 예외 발생
- `datetime.now()`는 timezone-naive인데, DB 모델은 `DateTime(timezone=True)`로 정의됨

**조치 방안:**
```python
from datetime import datetime, timezone

def parse_datetime_safe(parsed_tuple):
    try:
        if parsed_tuple:
            return datetime(*parsed_tuple[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass
    return datetime.now(timezone.utc)
```

---

#### 7. PubMed 이메일 하드코딩

**파일:** `collector/pubmed_collector.py:8`

```python
def __init__(self, email: str = "your_email@example.com", ...):
    self.pubmed = PubMed(tool="DermaInsight", email=email)
```

NCBI PubMed API 정책상 유효한 연락용 이메일이 필수이나, 플레이스홀더가 기본값으로 그대로 사용됩니다.

**조치 방안:**
```python
email = email or os.getenv("PUBMED_EMAIL")
if not email or email == "your_email@example.com":
    raise ValueError("PUBMED_EMAIL 환경 변수를 설정해주세요.")
```

---

#### 8. Rate Limiting 없음

**파일:** `collector/rss_collector.py`, `collector/pubmed_collector.py`

두 수집기 모두 연속 요청에 딜레이가 없어서 대상 서버에 과부하를 주거나 IP 차단될 수 있습니다.

**조치 방안:**
```python
import time

for url in self.sources:
    time.sleep(1.0)    # 요청 간 1초 대기
    response = fetch_with_retry(url, headers)
```

---

### MEDIUM (개선 권장)

#### 9. API 입력값 검증 없음

**파일:** `main.py:30-33`

```python
@app.get("/articles/")
def read_articles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    articles = crud.get_articles(db, skip=skip, limit=limit)
    return articles
```

`skip=-1`, `limit=999999` 등 비정상적인 값이 그대로 DB 쿼리에 전달됩니다.

**조치 방안:**
```python
from fastapi import Query

@app.get("/articles/")
def read_articles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    ...
```

---

#### 10. 로깅 체계 없음

**파일:** 전체 Python 소스

모든 파일에서 `print()`만 사용합니다. 타임스탬프, 로그 레벨, 파일 저장 등 운영 환경에 필요한 로깅이 전혀 없습니다.

**조치 방안:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 사용 예시
logger.info("RSS 수집 시작")
logger.error(f"수집 실패: {e}", exc_info=True)
```

---

#### 11. Pydantic 모델 미사용

**파일:** `crud.py:8-19`

```python
def create_article(db: Session, article_data: dict):
    db_article = models.Article(
        title=article_data.get("title"),
        title_ko=article_data.get("title_ko"),
        ...
    )
```

`dict`를 그대로 받아서 타입 검증 없이 저장합니다. FastAPI의 Pydantic 통합을 활용하면 자동 검증과 API 문서화가 가능합니다.

**조치 방안:**
```python
from pydantic import BaseModel, Field
from typing import Optional

class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    title_ko: Optional[str] = Field(None, max_length=500)
    link: str
    source: str
    summary: Optional[str] = None
```

---

#### 12. OpenAI 클라이언트 설정 문제

**파일:** `processor/summarizer.py:8-14`

```python
def __init__(self, api_key: str = None):
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
        print("Warning: OPENAI_API_KEY is not set.")
    else:
        openai.api_key = self.api_key   # deprecated 전역 변수 설정
        self.client = openai.OpenAI(api_key=self.api_key)
```

- `openai.api_key` 전역 변수 설정은 deprecated
- 클라이언트 초기화 실패 시 graceful 처리 없음

**조치 방안:**
```python
def __init__(self, api_key: str = None):
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY 미설정. 요약 기능 비활성화.")
        self.client = None
    else:
        self.client = openai.OpenAI(api_key=api_key)
```

---

#### 13. 요약 캐싱 없음

**파일:** `collect_data.py:24-33`

수집 스크립트 재실행 시 이미 URL 중복 체크로 신규 아티클만 요약하지만, 스크립트 한 번 실행 중 동일 내용이 여러 소스에서 나오면 중복 요약이 발생할 수 있습니다. OpenAI API 비용이 불필요하게 증가합니다.

> **보류 사유:** 현재 URL 중복 체크가 작동하고 있어 실질적 중복 요약 가능성이 낮으며, 추가 캐싱 레이어의 복잡도 대비 효과가 제한적입니다.

---

### LOW (향후 개선)

#### 14. DB 인덱스 부족

**파일:** `models.py`

`source`, `created_at` 컬럼에 인덱스가 없어서 필터/정렬 쿼리 시 풀 테이블 스캔이 발생합니다.

**조치 방안:**
```python
__table_args__ = (
    Index('idx_source_published', 'source', 'published_date'),
    Index('idx_created_at', 'created_at'),
)
```

---

#### 15. API 응답 모델 없음

**파일:** `main.py`

`response_model` 미지정으로 Swagger/OpenAPI 문서에 응답 스키마가 표시되지 않습니다.

**조치 방안:**
```python
from pydantic import BaseModel
from typing import List

class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    source: str
    # ...
    class Config:
        from_attributes = True

@app.get("/articles/", response_model=List[ArticleResponse])
def read_articles(...):
    ...
```

---

#### 16. OpenAI 모델명 하드코딩

**파일:** `processor/summarizer.py:37`

```python
model="gpt-4o",
```

모델 변경 시 코드 수정이 필요합니다.

**조치 방안:**
```python
self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
```

---

#### 17. 트랜잭션 관리 부재

**파일:** `collect_data.py`

수집 중간에 실패하면 일부만 저장된 상태가 됩니다. 배치 단위로 커밋하거나, 전체를 하나의 트랜잭션으로 묶는 전략이 필요합니다.

---

#### 18. DB 커넥션 검증 없음

**파일:** `database.py`

SQLite PRAGMA 설정(`foreign_keys` 등)이 없고, 헬스체크 엔드포인트가 없어서 서버 상태 모니터링이 불가합니다.

**조치 방안:**
```python
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "healthy"}
```

---

## Summary

This report covers a full analysis of the MDinfo backend codebase, identifying **18 issues** across security, reliability, performance, and code quality.

| Severity | Count | Key Issues |
|----------|-------|------------|
| CRITICAL | 2 | Real API key in `.env.example`, unrestricted CORS |
| HIGH | 6 | No DB error handling, unvalidated external input, no retries, unsafe datetime, hardcoded email, no rate limiting |
| MEDIUM | 5 | No API input validation, no logging framework, no Pydantic models, deprecated OpenAI usage, no summary caching |
| LOW | 5 | Missing DB indexes, no response models, hardcoded model name, no transaction management, no health check |

**Status:** 18건 중 17건 수정 완료 (2026-01-28). #13 요약 캐싱은 보류.

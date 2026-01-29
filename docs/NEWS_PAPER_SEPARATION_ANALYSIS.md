# 프론트엔드 뉴스/논문 분리 페이지 구현을 위한 상세 분석 보고서

## 목차
1. [현재 프론트엔드 구조 분석](#1-현재-프론트엔드-구조-분석)
2. [백엔드 API 분석](#2-백엔드-api-분석)
3. [데이터 소스 분류 분석](#3-데이터-소스-분류-분석)
4. [현재 문제점 식별](#4-현재-문제점-식별)
5. [개선 방안 제시](#5-개선-방안-제시)
6. [구현 체크리스트](#6-구현-체크리스트)
7. [예상 구현 결과](#7-예상-구현-결과)
8. [위험 요소 및 완화 방안](#8-위험-요소-및-완화-방안)
9. [성능 고려사항](#9-성능-고려사항)
10. [결론 및 권장사항](#10-결론-및-권장사항)

---

## 1. 현재 프론트엔드 구조 분석

### 1.1 디렉토리 구조
```
frontend/src/
├── app/
│   ├── layout.tsx          # Root 레이아웃 (메타데이터, 폰트 설정)
│   ├── globals.css         # 전역 스타일
│   ├── page.tsx            # 홈 페이지 (모든 기사 표시)
│   ├── feed.xml/
│   │   └── route.ts        # RSS 피드 생성
│   └── sitemap.ts          # 사이트맵 생성
├── components/
│   ├── ErrorBoundary.tsx
│   └── ThemeToggle.tsx
└── types.ts                # TypeScript 인터페이스
```

### 1.2 현재 page.tsx의 구현 방식

**주요 특징:**
- **클라이언트 컴포넌트** ('use client' 지정)
- **단일 페이지 구조**: 모든 기사를 하나의 페이지에서 표시
- **필터링 기능**:
  - 검색 (제목, 요약, 키워드)
  - 소스별 필터링 (동적으로 추출한 고유 소스 목록)
  - 정렬 (날짜 내림차순/오름차순, 소스순)
- **페이지네이션**: 무한 스크롤 방식의 "더 보기" 버튼
- **상태 관리**: useState를 통한 클라이언트 상태 관리

**현재 API 호출:**
```typescript
GET /articles/?skip={pageNum}&limit={ITEMS_PER_PAGE}
```

### 1.3 Article 인터페이스 (types.ts)
```typescript
interface Article {
    id: number;
    title: string;
    title_ko?: string;
    url: string;
    source: string;           // 현재는 단순 문자열 (구분자 없음)
    published_date: string;
    summary?: string;
    original_abstract?: string;
    keywords?: string;
    is_read?: boolean;
}
```

**문제점**: `source` 필드가 뉴스/논문을 구분할 정보를 포함하지 않음

### 1.4 현재 라우팅 구조
- **App Router 사용** (Next.js 16)
- **단일 라우트**: `/` (루트만 존재)
- **동적 라우트 미사용**

---

## 2. 백엔드 API 분석

### 2.1 API 엔드포인트

**현재 주요 엔드포인트:**
```python
GET /                           # 상태 확인
GET /articles/                  # 아티클 목록 조회 (필터링, 검색 지원)
GET /health                     # 헬스 체크
GET /scheduler/status           # 스케줄러 상태
```

**GET /articles/ 쿼리 파라미터:**
- `skip`: 건너뛸 항목 수
- `limit`: 반환할 최대 항목 수 (기본값: 20, 최대: 100)
- `source`: 소스별 필터링 (선택사항)
- `search`: 제목/요약 검색 (선택사항)

**응답 형식 (PaginatedResponse):**
```python
{
    "items": [Article, ...],
    "total": int,
    "skip": int,
    "limit": int,
    "has_more": bool
}
```

### 2.2 schemas.py의 ArticleResponse 구조
```python
class ArticleResponse(BaseModel):
    id: int
    title: Optional[str] = None
    title_ko: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None          # 추가 정보 없음
    published_date: Optional[datetime] = None
    summary: Optional[str] = None
    original_abstract: Optional[str] = None
    keywords: Optional[str] = None
    created_at: Optional[datetime] = None
    is_read: Optional[bool] = None
```

### 2.3 데이터베이스 모델 (models.py)
```python
class Article(Base):
    __tablename__ = "articles"
    id: int                          # PK
    title: str
    title_ko: str (nullable)
    url: str (unique)
    source: str                      # 문자열만 저장됨
    published_date: datetime
    summary: text (nullable)
    original_abstract: text (nullable)
    keywords: str (nullable)
    created_at: datetime
    is_read: bool (default: False)
```

### 2.4 필터링/검색 기능 (crud.py)
```python
def get_articles_filtered(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,      # 부분 일치 (ilike)
    search: Optional[str] = None,       # 제목, 한글 제목, 요약에서 검색
) -> tuple[int, List[Article]]
```

---

## 3. 데이터 소스 분류 분석

### 3.1 sources.json의 데이터 소스 구조

**RSS 피드 (8개):**
```json
{
    "rss_feeds": [
        {
            "name": "Dermatology Times",
            "url": "https://www.dermatologytimes.com/rss",
            "category": "News"
        },
        {
            "name": "Journal of Cosmetic Dermatology",
            "url": "https://onlinelibrary.wiley.com/feed/14732165/most-recent",
            "category": "Journal"
        }
    ]
}
```

**PubMed 검색 쿼리 (11개):**
- skin rejuvenation, antiaging, aesthetic, botulinum toxin, skin booster, filler, exosome, HIFU, microneedling, RF, dermatology

**Google Scholar 키워드 (11개):**
- (PubMed와 동일)

### 3.2 뉴스 vs 논문 분류

**뉴스 소스:**
1. "Dermatology Times" (News)
2. "의학신문" (News-KR)
3. "청년의사" (News-KR)
4. "뷰티경제" (News-KR)

**논문 소스:**
1. "Journal of Cosmetic Dermatology" (Journal)
2. "JEADV" (Journal)
3. "Lasers in Surgery and Medicine" (Journal)
4. "JAAD" (Journal)
5. "PubMed | {저널명}" (API - 동적 생성)
6. "Google Scholar | {저널명}" (Scholar - 동적 생성)

### 3.3 source 필드의 패턴 분석

**현재 저장 방식:**
- RSS 피드: 피드 타이틀 직접 저장 (예: "Dermatology Times")
- PubMed: "PubMed | {저널명}" 형식
- Scholar: "Google Scholar | {저널명}" 형식
- 한글 뉴스: "의학신문", "청년의사", "뷰티경제" 등

---

## 4. 현재 문제점 식별

### 4.1 뉴스와 논문 혼재 문제
- **단일 페이지에서 모든 콘텐츠 표시**: 사용자가 관심있는 타입(뉴스 또는 논문)을 쉽게 찾기 어려움
- **필터 UI의 한계**: 현재 소스 필터는 고유한 모든 소스를 드롭다운에 표시하므로 매우 길어짐
- **사용자 경험 저하**: 뉴스 찾는 사용자가 학술 논문 목록을 스크롤해야 함

### 4.2 데이터 구조의 한계
- **category 정보 부재**: Article 모델에 명시적인 카테고리/타입 필드 없음
- **소스 정보 일관성 부족**: RSS, PubMed, Scholar마다 다른 형식
- **sources.json의 category는 미사용**: 수집 과정에서 category 정보 활용 안 함

### 4.3 API의 한계
- **기본 필터링만 가능**: `source` 파라미터로는 "뉴스" vs "논문" 구분 불가능
- **확장성 부족**: 향후 다른 카테고리 추가 시 복잡도 증가

### 4.4 프론트엔드의 한계
- **라우팅 구조 단순**: 단일 페이지만 존재하여 URL 기반의 명확한 네비게이션 불가능
- **북마크/공유 불편**: 특정 카테고리 링크를 공유할 수 없음
- **상태 복구 불가**: 페이지 새로고침 시 필터 상태 손실

---

## 5. 개선 방안 제시

### 5.1 백엔드 개선 (높은 우선순위)

#### 5.1.1 데이터베이스 스키마 확장

**Article 모델 수정:**
```python
class Article(Base):
    __tablename__ = "articles"
    # ... 기존 필드

    # 새 필드 추가
    category = Column(String, index=True)  # 'news' 또는 'paper'
    source_type = Column(String)           # 'RSS', 'PubMed', 'Scholar'
```

**마이그레이션 전략:**
```sql
-- 1. NULL 기본값으로 새 필드 추가
ALTER TABLE articles ADD COLUMN category VARCHAR DEFAULT NULL;

-- 2. 기존 데이터 일괄 업데이트
UPDATE articles SET category = 'news'
WHERE source IN ('Dermatology Times', '의학신문', '청년의사', '뷰티경제');

UPDATE articles SET category = 'paper'
WHERE source IN ('Journal of Cosmetic Dermatology', 'JEADV', 'Lasers in Surgery and Medicine', 'JAAD')
   OR source LIKE 'PubMed %'
   OR source LIKE 'Google Scholar %';

-- 3. NULL 값 처리 (기본값: paper)
UPDATE articles SET category = 'paper' WHERE category IS NULL;

-- 4. NOT NULL 제약 추가
ALTER TABLE articles MODIFY COLUMN category VARCHAR NOT NULL DEFAULT 'paper';

-- 5. 인덱스 생성
CREATE INDEX idx_category ON articles(category);
CREATE INDEX idx_category_published ON articles(category, published_date);
```

#### 5.1.2 카테고리 분류 로직

**collect_data.py에 추가:**
```python
# 소스별 카테고리 매핑
NEWS_SOURCES = {
    "Dermatology Times",
    "의학신문",
    "청년의사",
    "뷰티경제",
}

def categorize_source(source_name: str) -> str:
    """소스명에서 카테고리 결정"""
    if any(news_source in source_name for news_source in NEWS_SOURCES):
        return "news"
    elif source_name.startswith("PubMed |") or source_name.startswith("Google Scholar |"):
        return "paper"
    # sources.json의 category 활용 가능
    return "paper"  # 기본값

# 수집 항목에 category 추가
item['category'] = categorize_source(item['source'])
```

#### 5.1.3 API 엔드포인트 확장

**main.py 수정:**
```python
@app.get("/articles/", response_model=PaginatedResponse[ArticleResponse])
def read_articles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(None, description="'news', 'paper', or 'all'"),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """아티클 목록 조회 (카테고리 필터링 지원)"""
    cache_key = f"articles:{skip}:{limit}:{category}:{source}:{search}"

    # 캐시 조회
    cached_result = get_cache().get(cache_key)
    if cached_result:
        return cached_result

    # DB 조회
    total, articles = crud.get_articles_filtered(
        db, skip=skip, limit=limit,
        category=category, source=source, search=search
    )

    result = PaginatedResponse(
        items=articles,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )

    get_cache().set(cache_key, result, ttl=300)
    return result
```

**crud.py 수정:**
```python
def get_articles_filtered(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
) -> tuple[int, List[Article]]:
    """필터링된 아티클 조회 (카테고리 지원)"""
    query = db.query(models.Article)

    # 카테고리 필터링
    if category and category in ('news', 'paper'):
        query = query.filter(models.Article.category == category)

    # 소스 필터링
    if source:
        query = query.filter(models.Article.source.ilike(f"%{source}%"))

    # 검색 필터링
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.Article.title.ilike(search_pattern),
                models.Article.title_ko.ilike(search_pattern),
                models.Article.summary.ilike(search_pattern),
            )
        )

    total = query.count()
    articles = (
        query.order_by(models.Article.published_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return total, articles
```

#### 5.1.4 Article 응답 스키마 확장

**schemas.py:**
```python
class ArticleResponse(BaseModel):
    id: int
    title: Optional[str] = None
    title_ko: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None      # 'news' 또는 'paper'
    source_type: Optional[str] = None   # 'RSS', 'PubMed', 'Scholar'
    published_date: Optional[datetime] = None
    summary: Optional[str] = None
    original_abstract: Optional[str] = None
    keywords: Optional[str] = None
    created_at: Optional[datetime] = None
    is_read: Optional[bool] = None

    model_config = {"from_attributes": True}
```

---

### 5.2 프론트엔드 개선 (높은 우선순위)

#### 5.2.1 새로운 라우팅 구조

**목표 라우트:**
```
/              → 모든 기사 (현재 페이지 유지)
/news          → 뉴스만 표시
/papers        → 논문만 표시
```

**새 디렉토리 구조:**
```
frontend/src/app/
├── layout.tsx              # Root 레이아웃 (유지)
├── globals.css             # 전역 스타일 (유지)
├── page.tsx                # 홈 페이지: 모든 기사
├── news/
│   └── page.tsx            # 뉴스 페이지
├── papers/
│   └── page.tsx            # 논문 페이지
└── components/
    ├── ArticleGrid.tsx     # 공용 기사 그리드 컴포넌트
    ├── ArticleCard.tsx     # 공용 기사 카드 컴포넌트
    ├── Toolbar.tsx         # 공용 필터/검색 도구
    ├── Navigation.tsx      # 새로 추가: 탭 네비게이션
    ├── ThemeToggle.tsx     # 기존
    └── ErrorBoundary.tsx   # 기존
```

#### 5.2.2 타입 정의 업데이트 (types.ts)

```typescript
export type ArticleCategory = 'news' | 'paper';
export type SourceType = 'RSS' | 'PubMed' | 'Scholar';

export interface Article {
    id: number;
    title: string;
    title_ko?: string;
    url: string;
    source: string;
    category?: ArticleCategory;           // 새 필드
    source_type?: SourceType;             // 새 필드
    published_date: string;
    summary?: string;
    original_abstract?: string;
    keywords?: string;
    is_read?: boolean;
}

export interface PaginatedResponse {
    items: Article[];
    total: number;
    skip: number;
    limit: number;
    has_more: boolean;
}
```

#### 5.2.3 공용 컴포넌트 추출

**Navigation.tsx (새로운 탭 네비게이션):**
```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
    const pathname = usePathname();

    return (
        <nav className="category-tabs" role="navigation" aria-label="카테고리 네비게이션">
            <Link
                href="/"
                className={pathname === '/' ? 'active' : ''}
                aria-current={pathname === '/' ? 'page' : undefined}
            >
                전체
            </Link>
            <Link
                href="/news"
                className={pathname === '/news' ? 'active' : ''}
                aria-current={pathname === '/news' ? 'page' : undefined}
            >
                뉴스
            </Link>
            <Link
                href="/papers"
                className={pathname === '/papers' ? 'active' : ''}
                aria-current={pathname === '/papers' ? 'page' : undefined}
            >
                논문
            </Link>
        </nav>
    );
}
```

**ArticleCard.tsx (공용 카드 컴포넌트):**
```typescript
'use client';

import { Article } from '@/types';

interface ArticleCardProps {
    article: Article;
}

export default function ArticleCard({ article }: ArticleCardProps) {
    return (
        <article className="card">
            <div className="card-header">
                <div>
                    <span className="source-tag">{article.source}</span>
                    {article.category && (
                        <span className={`category-badge ${article.category}`}>
                            {article.category === 'news' ? '뉴스' : '논문'}
                        </span>
                    )}
                    <span className="date">
                        <time dateTime={article.published_date}>
                            {new Date(article.published_date).toLocaleDateString('ko-KR')}
                        </time>
                    </span>
                </div>
                <button
                    className="share-button"
                    onClick={() => {
                        navigator.clipboard.writeText(article.url);
                        alert('링크가 복사되었습니다!');
                    }}
                    aria-label="링크 복사"
                    title="링크 복사"
                >
                    🔗
                </button>
            </div>
            <h2>
                <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="external-link"
                >
                    {article.title_ko || article.title}
                    <span className="sr-only"> (새 탭에서 열림)</span>
                </a>
            </h2>
            {article.title_ko && article.title !== article.title_ko && (
                <div className="original-title">{article.title}</div>
            )}
            {article.summary && (
                <div className="summary-box">
                    <strong className="summary-label">
                        <span role="img" aria-label="전구 아이콘">💡</span> AI 요약
                    </strong>
                    {article.summary}
                </div>
            )}
            <div className="keywords-container">
                {article.keywords?.split(',').filter(Boolean).map((k, i) => (
                    <span key={i} className="keyword-tag">#{k.trim()}</span>
                ))}
            </div>
        </article>
    );
}
```

#### 5.2.4 각 페이지 구현

**news/page.tsx (뉴스 페이지):**
```typescript
'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { Article, PaginatedResponse, isPaginatedResponse } from '@/types';
import ArticleCard from '@/components/ArticleCard';
import Navigation from '@/components/Navigation';
import { ThemeToggle } from '@/components/ThemeToggle';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ITEMS_PER_PAGE = 12;

export default function NewsPage() {
    const [articles, setArticles] = useState<Article[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);

    const fetchArticles = useCallback(async (pageNum: number, append = false) => {
        setLoading(true);
        setError(null);

        try {
            const skip = pageNum * ITEMS_PER_PAGE;
            const res = await fetch(
                `${API_URL}/articles/?skip=${skip}&limit=${ITEMS_PER_PAGE}&category=news`
            );

            if (!res.ok) {
                throw new Error(`서버 오류: ${res.status}`);
            }

            const data: unknown = await res.json();
            if (!isPaginatedResponse(data)) {
                throw new Error('잘못된 응답 형식입니다.');
            }

            if (append) {
                setArticles(prev => [...prev, ...data.items]);
            } else {
                setArticles(data.items);
            }

            setHasMore(data.has_more);
        } catch (err) {
            setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchArticles(0);
    }, [fetchArticles]);

    const loadMore = () => {
        const nextPage = page + 1;
        setPage(nextPage);
        fetchArticles(nextPage, true);
    };

    if (error && articles.length === 0) {
        return (
            <main id="main-content" className="error-state">
                <div className="error-content" role="alert">
                    <h2>오류가 발생했습니다</h2>
                    <p>{error}</p>
                    <button onClick={() => fetchArticles(0)} className="retry-button">
                        다시 시도
                    </button>
                </div>
            </main>
        );
    }

    return (
        <main id="main-content">
            <header className="header-with-toggle">
                <div>
                    <h1>Derma-Insight - 뉴스</h1>
                    <p>피부과/미용 업계 뉴스</p>
                </div>
                <ThemeToggle />
            </header>

            <Navigation />

            {loading && articles.length === 0 ? (
                <div className="skeleton-grid" aria-label="로딩 중" role="status">
                    {[...Array(6)].map((_, i) => (
                        <div key={i} className="skeleton-card">
                            <div className="skeleton-line skeleton-tag" />
                            <div className="skeleton-line skeleton-title" />
                            <div className="skeleton-line skeleton-title-short" />
                            <div className="skeleton-line skeleton-text" />
                        </div>
                    ))}
                </div>
            ) : articles.length === 0 ? (
                <div className="empty-state">
                    <h2>아직 수집된 뉴스가 없습니다</h2>
                    <p>데이터 수집 파이프라인을 실행해 주세요.</p>
                </div>
            ) : (
                <section aria-label="뉴스 목록">
                    <p className="results-info">{articles.length}개 뉴스</p>
                    <div className="card-grid">
                        {articles.map((article) => (
                            <ArticleCard key={article.id} article={article} />
                        ))}
                    </div>

                    {hasMore && (
                        <div className="load-more-container">
                            <button
                                onClick={loadMore}
                                disabled={loading}
                                className="load-more-button"
                            >
                                {loading ? '로딩 중...' : '더 보기'}
                            </button>
                        </div>
                    )}
                </section>
            )}
        </main>
    );
}
```

**papers/page.tsx (논문 페이지):**
```typescript
// news/page.tsx와 거의 동일
// 차이점:
// 1. 제목: "Derma-Insight - 논문"
// 2. 설명: "피부과/미용 연구 논문"
// 3. API 호출: category=paper
```

#### 5.2.5 글로벌 스타일 확장 (globals.css)

```css
/* 카테고리 탭 네비게이션 */
.category-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid var(--accent);
}

.category-tabs a {
  padding: 0.75rem 1.5rem;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  color: var(--text);
}

.category-tabs a:hover {
  border-bottom-color: var(--primary);
  color: var(--primary);
}

.category-tabs a.active {
  border-bottom-color: var(--primary);
  color: var(--primary);
  font-weight: 600;
}

/* 카테고리 뱃지 */
.category-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.5rem;
}

.category-badge.news {
  background-color: #e3f2fd;
  color: #1976d2;
}

.category-badge.paper {
  background-color: #f3e5f5;
  color: #7b1fa2;
}

/* 다크 모드 */
[data-theme="dark"] .category-badge.news {
  background-color: #1565c0;
  color: #bbdefb;
}

[data-theme="dark"] .category-badge.paper {
  background-color: #6a1b9a;
  color: #e1bee7;
}

/* 반응형 */
@media (max-width: 600px) {
  .category-tabs {
    flex-wrap: wrap;
  }

  .category-tabs a {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }
}
```

---

## 6. 구현 체크리스트

> **업데이트: 2026-01-29** - Phase 1-3 완료, Phase 4 부분 완료

### Phase 1: 데이터 기초 구축 ✅ 완료
- [x] Article 모델에 `category` 필드 추가
- [x] 데이터베이스 마이그레이션 SQL 작성 및 실행
- [x] 기존 데이터 분류 (소스명 기반 자동 분류)
- [x] `category` 인덱스 생성
- [x] collect_data.py에 카테고리 로직 추가
- [x] 새 데이터 수집 시 category 자동 할당 확인

### Phase 2: 백엔드 API 확장 ✅ 완료
- [x] crud.py의 get_articles_filtered()에 category 파라미터 추가
- [x] main.py의 GET /articles/에 category 쿼리 파라미터 추가
- [x] schemas.py의 ArticleResponse에 category 필드 추가
- [x] 캐시 키에 category 포함
- [x] API 테스트 (curl/Postman)
  - [x] GET /articles/?category=news
  - [x] GET /articles/?category=paper
  - [x] GET /articles/?category=all

### Phase 3: 프론트엔드 기본 구조 ✅ 완료
- [x] types.ts 업데이트 (ArticleCategory, Article 인터페이스)
- [x] ArticleCard 컴포넌트 작성
- [x] Navigation 컴포넌트 작성
- [x] news/ 디렉토리 및 page.tsx 생성
- [x] papers/ 디렉토리 및 page.tsx 생성
- [x] globals.css에 탭 스타일 추가

### Phase 4: 페이지별 구현 ✅ 완료
- [x] news/page.tsx 완성
- [x] papers/page.tsx 완성
- [x] page.tsx(홈)에 Navigation 추가
- [ ] 각 페이지의 메타데이터 설정 (향후 작업)
- [ ] SEO 최적화 (title, description) (향후 작업)

### Phase 5: 테스트 및 최적화 🔄 진행 중
- [x] 각 페이지 기능 테스트 (빌드 성공)
- [x] 필터링/검색 동작 확인
- [ ] 반응형 디자인 검증 (모바일, 태블릿, 데스크톱)
- [ ] 다크/라이트 테마 확인
- [ ] 브라우저 호환성 테스트
- [ ] 성능 최적화 (Lighthouse 점수 확인)
- [ ] 접근성 검증 (WCAG)

---

## 7. 예상 구현 결과

### 사용자 경험 개선

**Before:**
```
/ (단일 페이지)
├─ 모든 기사 (뉴스 + 논문 혼재)
├─ 필터: 모든 소스 (수십 개)
├─ 검색 후 많은 결과 스크롤 필요
└─ 특정 타입만 보기 어려움
```

**After:**
```
/               → 모든 기사
/news           → 뉴스만 (명확한 구분)
/papers         → 논문만 (학술 콘텐츠)

각 페이지:
├─ 탭 네비게이션으로 쉬운 이동
├─ 카테고리별 최적화된 콘텐츠
├─ URL 북마크/공유 가능
└─ 명확한 정보 구조
```

### 데이터 구조 개선

**Before:**
```python
Article {
    source: "Dermatology Times"  # 뉴스인지 논문인지 불명확
}
```

**After:**
```python
Article {
    source: "Dermatology Times",
    category: "news",           # 명확한 분류
    source_type: "RSS"          # 데이터 출처
}
```

---

## 8. 위험 요소 및 완화 방안

| 위험 | 영향 | 완화 방안 |
|------|------|---------|
| 기존 데이터 마이그레이션 실패 | 높음 | 사전 백업 및 롤백 계획, 스테이징 환경 테스트 |
| API 하위호환성 문제 | 중간 | category 필드를 선택사항으로 유지 |
| 성능 저하 | 중간 | 인덱스 추가, 쿼리 최적화, 캐싱 강화 |
| 프론트엔드 번들 크기 증가 | 낮음 | 컴포넌트 분할 및 동적 임포트 |
| SEO 영향 | 중간 | sitemap.xml 업데이트, robots.txt 확인 |

---

## 9. 성능 고려사항

### 데이터베이스 최적화
```python
# 추천 인덱스
Index('idx_category', 'category')
Index('idx_category_published', 'category', 'published_date')
Index('idx_source_category', 'source', 'category')
```

### 캐싱 전략
```python
# 카테고리별로 별도 캐시 키
cache_key = f"articles:category:{category}:skip:{skip}:limit:{limit}"
# TTL: 5-10분
```

### 프론트엔드 최적화
- 각 페이지는 독립적으로 데이터 페칭
- React 18의 Suspense 활용 고려
- 이미지 최적화 및 레이지 로딩
- 코드 스플리팅 (Next.js 자동)

---

## 10. 결론 및 권장사항

### 핵심 권장사항

1. **즉시 구현 필요 (P0):**
   - ✅ Article 모델에 category 필드 추가
   - ✅ 데이터 마이그레이션 실행
   - ✅ API 필터 확장 (category 파라미터)

2. **우선순위 높음 (P1):**
   - ✅ 프론트엔드 라우팅 구조 개선 (/news, /papers)
   - ✅ Navigation 탭 추가
   - ✅ 공용 컴포넌트 추출

3. **향후 계획 (P2):**
   - 상세 페이지 구현 (/news/[id], /papers/[id])
   - 사용자 선호 카테고리 저장 (localStorage/쿠키)
   - RSS 피드 카테고리별 생성 (/news/feed.xml, /papers/feed.xml)
   - 통계/인사이트 대시보드

### 예상 효과

- **사용자 만족도 향상**: 원하는 콘텐츠를 빠르게 찾을 수 있음
- **SEO 개선**: 각 카테고리별 전용 페이지로 검색 최적화
- **확장성 증가**: 향후 더 많은 카테고리 추가 용이
- **유지보수성 향상**: 명확한 데이터 구조로 버그 감소
- **전문성 강화**: 뉴스/논문 구분으로 학술적 신뢰도 증가

### 구현 타임라인

| 단계 | 예상 소요 | 핵심 작업 |
|------|---------|---------|
| Phase 1 | 1-2일 | 데이터 모델 및 마이그레이션 |
| Phase 2 | 1일 | 백엔드 API 확장 |
| Phase 3 | 2-3일 | 프론트엔드 구조 구축 |
| Phase 4 | 2-3일 | 페이지별 구현 |
| Phase 5 | 1-2일 | 테스트 및 최적화 |
| **총합** | **7-11일** | **완전한 구현** |

---

### 문서 정보

- **작성일**: 2026-01-29
- **버전**: 1.0
- **분석 대상**: MDinfo (Derma-Insight) v1.0
- **기술 스택**: Next.js 16 / React 19 / FastAPI / SQLite
- **분석 수준**: Very Thorough
- **작성자**: AI Analysis Agent

'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { Article, isArticleArray } from '../types';
import { ThemeToggle } from '@/components/ThemeToggle';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ITEMS_PER_PAGE = 12;
const FETCH_TIMEOUT = 10000; // 10초

type SortOption = 'date-desc' | 'date-asc' | 'source';

/** 에러 타입에 따른 사용자 친화적 메시지 반환 */
function getErrorMessage(error: unknown): string {
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return '서버에 연결할 수 없습니다. 네트워크 연결을 확인하거나 백엔드 서버가 실행 중인지 확인해 주세요.';
  }
  if (error instanceof DOMException && error.name === 'AbortError') {
    return '요청 시간이 초과되었습니다. 네트워크 상태를 확인해 주세요.';
  }
  if (error instanceof Error) {
    if (error.message.includes('CORS') || error.message.includes('cross-origin')) {
      return 'CORS 오류가 발생했습니다. 백엔드 서버의 CORS 설정을 확인해 주세요.';
    }
    return error.message;
  }
  return '데이터를 불러오는데 실패했습니다.';
}

/** 필수 필드가 있는 유효한 Article인지 검증 */
function isValidArticle(article: Article): boolean {
  return Boolean(article.id && article.title && article.url && article.source);
}

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [totalLoaded, setTotalLoaded] = useState(0);

  // 검색, 필터, 정렬 상태
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [sortOption, setSortOption] = useState<SortOption>('date-desc');

  // 고유 소스 목록 추출
  const sources = useMemo(() => {
    const uniqueSources = [...new Set(articles.map(a => a.source))];
    return uniqueSources.sort();
  }, [articles]);

  // 필터링 및 정렬된 기사 목록
  const filteredArticles = useMemo(() => {
    let result = [...articles];

    // 검색 필터
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(article =>
        (article.title_ko || article.title).toLowerCase().includes(query) ||
        article.summary?.toLowerCase().includes(query) ||
        article.keywords?.toLowerCase().includes(query)
      );
    }

    // 소스 필터
    if (selectedSource !== 'all') {
      result = result.filter(article => article.source === selectedSource);
    }

    // 정렬
    result.sort((a, b) => {
      switch (sortOption) {
        case 'date-desc':
          return new Date(b.published_date).getTime() - new Date(a.published_date).getTime();
        case 'date-asc':
          return new Date(a.published_date).getTime() - new Date(b.published_date).getTime();
        case 'source':
          return a.source.localeCompare(b.source);
        default:
          return 0;
      }
    });

    return result;
  }, [articles, searchQuery, selectedSource, sortOption]);

  const fetchArticles = useCallback(async (pageNum: number, append = false) => {
    setLoading(true);
    setError(null);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);

    try {
      const skip = pageNum * ITEMS_PER_PAGE;
      const res = await fetch(
        `${API_URL}/articles/?skip=${skip}&limit=${ITEMS_PER_PAGE}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`서버 오류: ${res.status}`);
      }

      const data: unknown = await res.json();
      if (!isArticleArray(data)) {
        throw new Error('잘못된 응답 형식입니다.');
      }

      // 필수 필드 검증 후 유효한 데이터만 사용
      const validArticles = data.filter(isValidArticle);

      if (append) {
        setArticles(prev => [...prev, ...validArticles]);
      } else {
        setArticles(validArticles);
      }

      setHasMore(data.length === ITEMS_PER_PAGE);
      setTotalLoaded(prev => append ? prev + validArticles.length : validArticles.length);
    } catch (err) {
      clearTimeout(timeoutId);
      setError(getErrorMessage(err));
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

  const isInitialLoading = loading && articles.length === 0;

  if (isInitialLoading) {
    return (
      <main id="main-content">
        <header className="header-with-toggle">
          <div>
            <h1>Derma-Insight</h1>
            <p>피부과/미용 연구 뉴스</p>
          </div>
          <ThemeToggle />
        </header>
        <div className="skeleton-grid" aria-label="로딩 중" role="status">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton-card">
              <div className="skeleton-line skeleton-tag" />
              <div className="skeleton-line skeleton-title" />
              <div className="skeleton-line skeleton-title-short" />
              <div className="skeleton-line skeleton-text" />
              <div className="skeleton-keywords">
                <div className="skeleton-line skeleton-keyword" />
                <div className="skeleton-line skeleton-keyword" />
                <div className="skeleton-line skeleton-keyword" />
              </div>
            </div>
          ))}
        </div>
      </main>
    );
  }

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
      <header>
        <h1>Derma-Insight</h1>
        <p>피부과/미용 연구 뉴스</p>
      </header>

      {/* 검색 및 필터 UI */}
      {articles.length > 0 && (
        <div className="toolbar">
          <div className="search-box">
            <input
              type="search"
              placeholder="제목, 요약, 키워드 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
              aria-label="기사 검색"
            />
          </div>
          <div className="filter-group">
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="filter-select"
              aria-label="소스 필터"
            >
              <option value="all">모든 소스</option>
              {sources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
            <select
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value as SortOption)}
              className="filter-select"
              aria-label="정렬 옵션"
            >
              <option value="date-desc">최신순</option>
              <option value="date-asc">오래된순</option>
              <option value="source">소스순</option>
            </select>
          </div>
        </div>
      )}

      {articles.length === 0 && !loading ? (
        <div className="empty-state">
          <h2>아직 수집된 기사가 없습니다</h2>
          <p>데이터 수집 파이프라인을 실행해 주세요.</p>
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="empty-state">
          <h2>검색 결과가 없습니다</h2>
          <p>다른 검색어나 필터를 시도해 보세요.</p>
        </div>
      ) : (
        <section aria-label="기사 목록">
          <p className="results-info">{filteredArticles.length}개 기사</p>
          <div className="card-grid">
            {filteredArticles.map((article) => (
              <article key={article.id} className="card">
                <div className="card-header">
                  <div>
                    <span className="source-tag">{article.source}</span>
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
            ))}
          </div>

          {hasMore && !searchQuery && selectedSource === 'all' && (
            <div className="load-more-container">
              <button
                onClick={loadMore}
                disabled={loading}
                className="load-more-button"
              >
                {loading ? '로딩 중...' : '더 보기'}
              </button>
              <p className="load-more-info">{totalLoaded}개 기사 로드됨</p>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

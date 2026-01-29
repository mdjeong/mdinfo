'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { Article, PaginatedResponse, isPaginatedResponse } from '@/types';
import ArticleCard from '@/components/ArticleCard';
import Navigation from '@/components/Navigation';
import { ThemeToggle } from '@/components/ThemeToggle';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ITEMS_PER_PAGE = 12;
const FETCH_TIMEOUT = 10000;

type SortOption = 'date-desc' | 'date-asc' | 'source';

function getErrorMessage(error: unknown): string {
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return '서버에 연결할 수 없습니다. 네트워크 연결을 확인하거나 백엔드 서버가 실행 중인지 확인해 주세요.';
  }
  if (error instanceof DOMException && error.name === 'AbortError') {
    return '요청 시간이 초과되었습니다. 네트워크 상태를 확인해 주세요.';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return '데이터를 불러오는데 실패했습니다.';
}

function isValidArticle(article: Article): boolean {
  return Boolean(article.id && article.title && article.url && article.source);
}

export default function NewsPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [totalLoaded, setTotalLoaded] = useState(0);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [sortOption, setSortOption] = useState<SortOption>('date-desc');

  const sources = useMemo(() => {
    const uniqueSources = [...new Set(articles.map(a => a.source))];
    return uniqueSources.sort();
  }, [articles]);

  const filteredArticles = useMemo(() => {
    let result = [...articles];

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(article =>
        (article.title_ko || article.title).toLowerCase().includes(query) ||
        article.summary?.toLowerCase().includes(query) ||
        article.keywords?.toLowerCase().includes(query)
      );
    }

    if (selectedSource !== 'all') {
      result = result.filter(article => article.source === selectedSource);
    }

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
        `${API_URL}/articles/?skip=${skip}&limit=${ITEMS_PER_PAGE}&category=news`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`서버 오류: ${res.status}`);
      }

      const data: unknown = await res.json();
      if (!isPaginatedResponse(data)) {
        throw new Error('잘못된 응답 형식입니다.');
      }

      const validArticles = data.items.filter(isValidArticle);

      if (append) {
        setArticles(prev => [...prev, ...validArticles]);
      } else {
        setArticles(validArticles);
      }

      setHasMore(data.has_more);
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
            <h1>Derma-Insight - 뉴스</h1>
            <p>피부과/미용 업계 뉴스</p>
          </div>
          <ThemeToggle />
        </header>
        <Navigation />
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
      </main>
    );
  }

  if (error && articles.length === 0) {
    return (
      <main id="main-content" className="error-state">
        <header className="header-with-toggle">
          <div>
            <h1>Derma-Insight - 뉴스</h1>
            <p>피부과/미용 업계 뉴스</p>
          </div>
          <ThemeToggle />
        </header>
        <Navigation />
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
          <h2>아직 수집된 뉴스가 없습니다</h2>
          <p>데이터 수집 파이프라인을 실행해 주세요.</p>
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="empty-state">
          <h2>검색 결과가 없습니다</h2>
          <p>다른 검색어나 필터를 시도해 보세요.</p>
        </div>
      ) : (
        <section aria-label="뉴스 목록">
          <p className="results-info">{filteredArticles.length}개 뉴스</p>
          <div className="card-grid">
            {filteredArticles.map((article) => (
              <ArticleCard key={article.id} article={article} />
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
              <p className="load-more-info">{totalLoaded}개 뉴스 로드됨</p>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

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

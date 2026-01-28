'use client';

import { useEffect, useState } from 'react';
import { Article } from '../types';

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchArticles() {
      try {
        const res = await fetch('http://localhost:8000/articles/');
        const data = await res.json();
        setArticles(data);
      } catch (error) {
        console.error("Failed to fetch articles:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchArticles();
  }, []);

  if (loading) return <main>Loading...</main>;

  return (
    <main>
      <header>
        <h1>Derma-Insight</h1>
        <p>Latest Dermatology Research & News</p>
      </header>

      <div className="card-grid">
        {articles.map((article) => (
          <article key={article.id} className="card">
            <div>
              <span className="source-tag">{article.source}</span>
              <span className="date">{new Date(article.published_date).toLocaleDateString()}</span>
            </div>
            <h3>
              <a href={article.url} target="_blank" rel="noopener noreferrer">
                {article.title_ko || article.title}
              </a>
            </h3>
            {article.title_ko && article.title !== article.title_ko && (
                <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.5rem' }}>
                    {article.title}
                </div>
            )}
            {article.summary && (
              <div style={{ marginTop: '1rem', padding: '1rem', background: '#f9f9f9', borderRadius: '4px', fontSize: '0.95rem', lineHeight: '1.6' }}>
                <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#444' }}>💡 AI 요약</strong>
                {article.summary}
              </div>
            )}
            <div style={{ marginTop: '1rem' }}>
                {article.keywords && article.keywords.split(',').map((k, i) => (
                    <span key={i} className="keyword-tag">#{k.trim()}</span>
                ))}
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}

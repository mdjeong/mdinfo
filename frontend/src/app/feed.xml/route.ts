import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

interface Article {
  id: number;
  title: string;
  title_ko?: string;
  url: string;
  source: string;
  published_date: string;
  summary?: string;
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/articles/?limit=20`, {
      next: { revalidate: 3600 }, // 1시간 캐시
    });

    if (!res.ok) {
      throw new Error("Failed to fetch articles");
    }

    const articles: Article[] = await res.json();

    const rssItems = articles
      .map((article) => {
        const title = escapeXml(article.title_ko || article.title);
        const description = escapeXml(article.summary || "");
        const pubDate = new Date(article.published_date).toUTCString();

        return `
    <item>
      <title>${title}</title>
      <link>${escapeXml(article.url)}</link>
      <description>${description}</description>
      <pubDate>${pubDate}</pubDate>
      <source url="${escapeXml(article.url)}">${escapeXml(article.source)}</source>
      <guid isPermaLink="true">${escapeXml(article.url)}</guid>
    </item>`;
      })
      .join("");

    const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Derma-Insight | 피부과 연구 뉴스</title>
    <link>${SITE_URL}</link>
    <description>AI가 요약한 최신 피부과/미용 연구 논문과 업계 뉴스</description>
    <language>ko</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    ${rssItems}
  </channel>
</rss>`;

    return new NextResponse(rss, {
      headers: {
        "Content-Type": "application/xml",
        "Cache-Control": "public, max-age=3600, s-maxage=3600",
      },
    });
  } catch {
    return new NextResponse("Error generating RSS feed", { status: 500 });
  }
}

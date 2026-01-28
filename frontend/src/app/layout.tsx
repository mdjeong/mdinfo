import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  title: {
    default: "Derma-Insight | 피부과 연구 뉴스",
    template: "%s | Derma-Insight",
  },
  description: "AI가 요약한 최신 피부과/미용 연구 논문과 업계 뉴스를 한국어로 제공합니다.",
  keywords: ["피부과", "미용", "연구", "논문", "뉴스", "AI 요약", "dermatology", "aesthetics"],
  authors: [{ name: "Derma-Insight" }],
  creator: "Derma-Insight",
  metadataBase: new URL(SITE_URL),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: "ko_KR",
    url: SITE_URL,
    siteName: "Derma-Insight",
    title: "Derma-Insight | 피부과 연구 뉴스",
    description: "AI가 요약한 최신 피부과/미용 연구 논문과 업계 뉴스를 한국어로 제공합니다.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Derma-Insight - 피부과 연구 뉴스",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Derma-Insight | 피부과 연구 뉴스",
    description: "AI가 요약한 최신 피부과/미용 연구 논문과 업계 뉴스를 한국어로 제공합니다.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "Derma-Insight",
  description: "AI가 요약한 최신 피부과/미용 연구 논문과 업계 뉴스",
  url: SITE_URL,
  inLanguage: "ko-KR",
  publisher: {
    "@type": "Organization",
    name: "Derma-Insight",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <head>
        <link rel="preconnect" href={API_URL} />
        <link rel="dns-prefetch" href={API_URL} />
        <link
          rel="alternate"
          type="application/rss+xml"
          title="Derma-Insight RSS Feed"
          href="/feed.xml"
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <a href="#main-content" className="skip-link">
          본문으로 바로가기
        </a>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  );
}

export interface Article {
    id: number;
    title: string;
    title_ko?: string;
    url: string;
    source: string;
    published_date: string;
    summary?: string;
    original_abstract?: string;
    keywords?: string;
    is_read?: boolean;
}

/** API 응답이 Article 배열인지 검증 */
export function isArticleArray(data: unknown): data is Article[] {
    if (!Array.isArray(data)) return false;
    if (data.length === 0) return true;
    const first = data[0];
    return (
        typeof first === 'object' &&
        first !== null &&
        'id' in first &&
        'title' in first &&
        'url' in first &&
        'source' in first &&
        'published_date' in first
    );
}

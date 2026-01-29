export type ArticleCategory = 'news' | 'paper';
export type SourceType = 'RSS' | 'PubMed' | 'Scholar';

export interface Article {
    id: number;
    title: string;
    title_ko?: string;
    url: string;
    source: string;
    category?: ArticleCategory;
    source_type?: SourceType;
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

/** API 응답이 PaginatedResponse인지 검증 */
export function isPaginatedResponse(data: unknown): data is PaginatedResponse {
    if (typeof data !== 'object' || data === null) return false;
    const obj = data as Record<string, unknown>;
    return (
        'items' in obj &&
        Array.isArray(obj.items) &&
        'total' in obj &&
        typeof obj.total === 'number' &&
        'skip' in obj &&
        typeof obj.skip === 'number' &&
        'limit' in obj &&
        typeof obj.limit === 'number' &&
        'has_more' in obj &&
        typeof obj.has_more === 'boolean'
    );
}

/** API 응답이 Article 배열인지 검증 (하위 호환성) */
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

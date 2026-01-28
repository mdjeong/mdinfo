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
    is_read: boolean;
}

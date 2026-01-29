from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List
from datetime import datetime

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """표준 API 응답 형식"""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답 형식"""

    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool


class ArticleResponse(BaseModel):
    id: int
    title: Optional[str] = None
    title_ko: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None  # 'news' or 'paper'
    source_type: Optional[str] = None  # 'RSS', 'PubMed', 'Scholar'
    published_date: Optional[datetime] = None
    summary: Optional[str] = None
    original_abstract: Optional[str] = None
    keywords: Optional[str] = None
    created_at: Optional[datetime] = None
    is_read: Optional[bool] = None

    model_config = {"from_attributes": True}

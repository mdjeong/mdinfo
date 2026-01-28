from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArticleResponse(BaseModel):
    id: int
    title: Optional[str] = None
    title_ko: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    published_date: Optional[datetime] = None
    summary: Optional[str] = None
    original_abstract: Optional[str] = None
    keywords: Optional[str] = None
    created_at: Optional[datetime] = None
    is_read: Optional[bool] = None

    model_config = {"from_attributes": True}

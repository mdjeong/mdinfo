from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from .database import Base

class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index('idx_source_published', 'source', 'published_date'),
        Index('idx_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    title_ko = Column(String, nullable=True) # Korean translation of the title
    url = Column(String, unique=True, index=True)
    source = Column(String)  # PubMed, RSS, etc.
    published_date = Column(DateTime)
    summary = Column(Text, nullable=True)
    original_abstract = Column(Text, nullable=True)
    keywords = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)

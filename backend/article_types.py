"""타입 정의 모듈"""

from typing import TypedDict, Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


class ArticleDict(TypedDict, total=False):
    """수집된 아티클 딕셔너리 타입"""

    title: str
    link: str
    summary: str
    published: Optional[datetime]
    source: str
    source_type: str
    original_abstract: Optional[str]
    title_ko: Optional[str]
    keywords: Optional[str]
    doi: Optional[str]
    category: Optional[str]  # 'News', 'News-KR', 'Journal', 'Academic'


class SummaryResult(TypedDict):
    """요약 결과 타입"""

    title_ko: Optional[str]
    summary: Optional[str]


class CollectionResult(TypedDict):
    """수집 결과 타입"""

    rss: List[ArticleDict]
    pubmed: List[ArticleDict]
    scholar: List[ArticleDict]


@dataclass
class StageStats:
    """단계별 통계"""

    name: str
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineReport:
    """파이프라인 실행 리포트"""

    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    collection: Dict[str, StageStats] = field(default_factory=dict)
    summarization: Optional[StageStats] = None
    saving: Optional[StageStats] = None

    @property
    def duration_seconds(self) -> float:
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return 0.0

    @property
    def total_collected(self) -> int:
        return sum(s.success for s in self.collection.values())

    @property
    def total_saved(self) -> int:
        return self.saving.success if self.saving else 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "collection": {k: v.to_dict() for k, v in self.collection.items()},
            "summarization": self.summarization.to_dict() if self.summarization else None,
            "saving": self.saving.to_dict() if self.saving else None,
            "summary": {
                "total_collected": self.total_collected,
                "total_saved": self.total_saved,
            },
        }

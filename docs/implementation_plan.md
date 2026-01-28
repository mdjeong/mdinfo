# 구현 계획서 (Implementation Plan)

## 1. 개요 (Goal Description)
피부 미용 및 성형 분야의 최신 연구 논문, 산업 뉴스, 학회 소식 등을 자동으로 수집하고, AI를 활용해 요약 및 인사이트를 제공하는 웹 애플리케이션 'Derma-Insight (가칭)'를 구축합니다. 
`ideas-01.md`(소스)와 `ideas-02.md`(기능)를 기반으로 하여, 사용자가 손쉽게 최신 트렌드를 파악하고 원문 및 요약을 열람할 수 있도록 돕습니다.

## 2. 사용자 리뷰 필요 사항 (User Review Required)
> [!IMPORTANT]
> **기술 스택 확정**: 데이터 수집 및 분석에 강점이 있는 **Python (FastAPI)**을 백엔드로, 최신 웹 UI 구현을 위해 **Next.js (React)**를 프론트엔드로 사용하는 하이브리드 구조를 제안합니다. 동의하십니까?

> [!NOTE]
> **LLM API 사용**: 논문 요약을 위해 OpenAI (GPT-4o) 또는 유사한 API 사용이 필요하며, 이에 따른 비용이 발생할 수 있습니다. API 키 발급 준비가 필요합니다.

## 3. 제안된 변경 사항 (Proposed Changes)

### 시스템 아키텍처
- **Backend (Python)**:
    - **Data Collector**: `feedparser` (RSS), `paperscraper`/`BeautifulSoup` (Web), `pymed` (PubMed API).
    - **Processor**: 데이터 정제, LLM API 호출 (요약).
    - **Database**: SQLite (초기 개발용 단순함), 추후 PostgreSQL 확장 가능.
    - **API**: FastAPI를 통해 프론트엔드에 JSON 데이터 제공.
- **Frontend (Next.js)**:
    - 대시보드 형태의 UI.
    - 최신 뉴스 피드, 논문 검색/필터링, 상세 보기 모달/페이지.

### 디렉토리 구조
```
/mdinfo (Root)
  ├── backend/           # Python 서버 및 수집기
  │   ├── collector/     # 수집 모듈 (RSS, Api, Scraper)
  │   ├── processor/     # 요약 및 데이터 가공
  │   ├── main.py        # API 서버 진입점
  │   └── models.py      # DB 스키마
  ├── frontend/          # Next.js 웹 애플리케이션
  │   ├── app/           # 페이지 라우팅
  │   ├── components/    # UI 컴포넌트
  │   └── lib/           # 유틸리티 및 API 클라이언트
  └── docs/              # 프로젝트 문서 (한글 md)
```

### [Backend] Data Pipeline
#### [NEW] `backend/collector`
- `rss_collector.py`: 주요 저널 및 미디어 RSS 피드 수집.
- `pubmed_collector.py`: PubMed API를 이용한 키워드 기반 논문 탐색.
- `summarizer.py`: LLM을 이용해 수집된 텍스트(Abstract 등)를 구조화된 요약(한국어)으로 변환.

### [Frontend] User Interface
#### [NEW] `frontend`
- **Dashboard**: 카드 형태로 최신 콘텐츠 표시 (썸네일, 제목, 태그).
- **Detail View**: 원문 링크, PDF 다운로드(가능 시), 3줄 요약, 핵심 키워드 표시.
- **Search/Filter**: 날짜, 저널, 키워드(보톡스, 필러 등)별 필터링.

## 4. 검증 계획 (Verification Plan)

### 자동화 테스트
- **Backend**: `pytest`를 사용하여 RSS 파싱 및 API 응답 테스트.
- **Frontend**: 주요 UI 컴포넌트 렌더링 테스트.

### 수동 검증
- **수집**: 지정된 키워드("Exosome", "Lifting" 등)로 PubMed 데이터가 정상적으로 DB에 저장되는지 확인.
- **요약**: 저장된 논문의 요약문이 한국어로 자연스럽게 생성되었는지 검토.
- **웹앱**: 브라우저에서 대시보드가 로드되고, 필터링이 작동하는지 확인.

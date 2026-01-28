# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MDinfo (Derma-Insight) is a web application that automatically collects dermatology/aesthetics research papers and industry news, then generates Korean-language AI summaries. It has a Python/FastAPI backend and a Next.js/React frontend.

## Commands

### Backend (from `backend/`)
```bash
pip install -r requirements.txt          # Install Python dependencies
uvicorn main:app --reload --port 8000     # Run API server (dev)
python collect_data.py                    # Run data collection pipeline (RSS + PubMed + AI summarization)
pytest                                    # Run tests
```

### Frontend (from `frontend/`)
```bash
npm install       # Install dependencies
npm run dev       # Dev server on port 3000
npm run build     # Production build
npm run lint      # ESLint
```

## Architecture

### Data Pipeline
```
RSS Feeds (feedparser) ──┐
                         ├──→ OpenAI GPT-4o Summarizer (Korean) ──→ SQLite DB
PubMed API (pymed) ─────┘
```

`collect_data.py` orchestrates the pipeline: collectors fetch articles, the summarizer translates/summarizes to Korean via OpenAI, and results are stored in SQLite (`mdinfo.db`). Duplicate articles are skipped by URL uniqueness constraint.

### Backend (FastAPI)
- **`main.py`** — FastAPI app with CORS middleware. Serves `GET /articles/` (paginated, sorted by date desc).
- **`models.py`** — SQLAlchemy `Article` model (title, title_ko, url, source, summary, original_abstract, keywords, etc.)
- **`database.py`** — SQLite connection setup via SQLAlchemy
- **`crud.py`** — DB operations: create article, get by URL (dedup), list articles
- **`collector/rss_collector.py`** — Fetches RSS feeds defined in `sources.json`
- **`collector/pubmed_collector.py`** — Searches PubMed using queries from `sources.json`
- **`processor/summarizer.py`** — Calls OpenAI GPT-4o to produce Korean title + 300-char summary from English text

### Frontend (Next.js 16 / React 19)
- Uses App Router (`src/app/`)
- **`page.tsx`** — Client component that fetches from `http://localhost:8000/articles/` and renders article cards in a grid
- **`types.ts`** — `Article` TypeScript interface matching the backend model
- Path alias: `@/*` maps to `./src/*`

### Data Sources (`backend/sources.json`)
- 4 RSS feeds (MDedge Dermatology, Dermatology Times, etc.)
- 10 PubMed search queries (skin rejuvenation, botulinum toxin, exosome, HIFU, etc.)

## Environment

- Python virtual environment name: `mdinfo` (see `.python-version`)
- Requires `OPENAI_API_KEY` env var (loaded from `.env` via python-dotenv)
- Backend runs on port 8000, frontend on port 3000
- Frontend fetches from backend at `http://localhost:8000`
- All documentation and AI summaries are in Korean

---

## 프로젝트 개요

MDinfo(Derma-Insight)는 피부과/미용 분야의 최신 연구 논문과 업계 뉴스를 자동 수집하고, AI로 한국어 요약을 생성하는 웹 애플리케이션입니다. Python/FastAPI 백엔드와 Next.js/React 프론트엔드로 구성되어 있습니다.

## 명령어

### 백엔드 (`backend/` 디렉토리에서 실행)
```bash
pip install -r requirements.txt          # Python 의존성 설치
uvicorn main:app --reload --port 8000     # 개발 서버 실행
python collect_data.py                    # 데이터 수집 파이프라인 실행 (RSS + PubMed + AI 요약)
pytest                                    # 테스트 실행
```

### 프론트엔드 (`frontend/` 디렉토리에서 실행)
```bash
npm install       # 의존성 설치
npm run dev       # 개발 서버 (포트 3000)
npm run build     # 프로덕션 빌드
npm run lint      # ESLint 검사
```

## 아키텍처

### 데이터 파이프라인
```
RSS 피드 (feedparser) ──┐
                        ├──→ OpenAI GPT-4o 요약기 (한국어) ──→ SQLite DB
PubMed API (pymed) ────┘
```

`collect_data.py`가 파이프라인을 총괄합니다: 수집기가 아티클을 가져오고, 요약기가 OpenAI를 통해 한국어로 번역/요약하며, 결과는 SQLite(`mdinfo.db`)에 저장됩니다. 중복 아티클은 URL 고유성 제약으로 건너뜁니다.

### 백엔드 (FastAPI)
- **`main.py`** — CORS 미들웨어가 포함된 FastAPI 앱. `GET /articles/` 엔드포인트 제공 (페이지네이션, 날짜 역순 정렬)
- **`models.py`** — SQLAlchemy `Article` 모델 (title, title_ko, url, source, summary, original_abstract, keywords 등)
- **`database.py`** — SQLAlchemy를 통한 SQLite 연결 설정
- **`crud.py`** — DB 작업: 아티클 생성, URL로 조회(중복 확인), 아티클 목록 조회
- **`collector/rss_collector.py`** — `sources.json`에 정의된 RSS 피드 수집
- **`collector/pubmed_collector.py`** — `sources.json`의 쿼리로 PubMed 검색
- **`processor/summarizer.py`** — OpenAI GPT-4o를 호출하여 영문 텍스트에서 한국어 제목 + 300자 요약 생성

### 프론트엔드 (Next.js 16 / React 19)
- App Router 사용 (`src/app/`)
- **`page.tsx`** — `http://localhost:8000/articles/`에서 데이터를 가져와 아티클 카드 그리드로 렌더링하는 클라이언트 컴포넌트
- **`types.ts`** — 백엔드 모델과 일치하는 `Article` TypeScript 인터페이스
- 경로 별칭: `@/*` → `./src/*`

### 데이터 소스 (`backend/sources.json`)
- RSS 피드 4개 (MDedge Dermatology, Dermatology Times 등)
- PubMed 검색 쿼리 10개 (skin rejuvenation, botulinum toxin, exosome, HIFU 등)

## 환경 설정

- Python 가상환경 이름: `mdinfo` (`.python-version` 참조)
- `OPENAI_API_KEY` 환경 변수 필요 (`.env` 파일에서 python-dotenv로 로드)
- 백엔드: 포트 8000, 프론트엔드: 포트 3000
- 프론트엔드는 `http://localhost:8000`에서 백엔드 API를 호출
- 모든 문서 및 AI 요약은 한국어로 작성

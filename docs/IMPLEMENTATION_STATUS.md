# MDinfo (Derma-Insight) 구현 현황 보고서

**작성일**: 2026-01-29
**버전**: 1.0

---

## 1. 구현 완료 현황

### Phase 1: 데이터 기초 구축 ✅ 완료

| 항목 | 상태 | 설명 |
|------|------|------|
| Article 모델 수정 | ✅ | `category`, `source_type` 필드 추가 |
| DB 마이그레이션 | ✅ | 기존 데이터 자동 분류 완료 |
| 인덱스 생성 | ✅ | `idx_category`, `idx_category_published` |
| 수집 파이프라인 수정 | ✅ | `categorize_source()` 함수 추가 |
| 스키마 업데이트 | ✅ | `ArticleResponse`에 새 필드 추가 |

**주요 변경 파일:**
- `backend/models.py` - Article 모델에 category, source_type 필드 추가
- `backend/crud.py` - create_article()에 새 필드 저장 로직 추가
- `backend/schemas.py` - ArticleResponse에 category, source_type 추가
- `backend/collect_data.py` - categorize_source() 함수 및 카테고리 로직 추가

---

### Phase 2: 백엔드 API 확장 ✅ 완료

| 항목 | 상태 | 설명 |
|------|------|------|
| category 필터 파라미터 | ✅ | GET /articles/?category=news|paper |
| crud.py 수정 | ✅ | get_articles_filtered()에 category 파라미터 추가 |
| 캐시 키 업데이트 | ✅ | category 포함하여 캐싱 |
| API 테스트 | ✅ | news/paper 필터링 정상 동작 확인 |

**API 사용 예시:**
```bash
# 전체 기사
GET /articles/?skip=0&limit=20

# 뉴스만
GET /articles/?skip=0&limit=20&category=news

# 논문만
GET /articles/?skip=0&limit=20&category=paper

# 뉴스 + 검색
GET /articles/?skip=0&limit=20&category=news&search=피부
```

---

### Phase 3: 프론트엔드 구현 ✅ 완료

| 항목 | 상태 | 설명 |
|------|------|------|
| types.ts 업데이트 | ✅ | ArticleCategory, SourceType 타입 추가 |
| Navigation 컴포넌트 | ✅ | 전체/뉴스/논문 탭 네비게이션 |
| ArticleCard 컴포넌트 | ✅ | 재사용 가능한 카드 컴포넌트 |
| /news 페이지 | ✅ | 뉴스 전용 페이지 |
| /papers 페이지 | ✅ | 논문 전용 페이지 |
| 홈페이지 수정 | ✅ | Navigation, ArticleCard 통합 |
| 스타일 추가 | ✅ | 카테고리 탭, 뱃지 스타일 |

**현재 라우트 구조:**
```
frontend/src/app/
├── page.tsx            # / (전체 기사)
├── news/
│   └── page.tsx        # /news (뉴스만)
├── papers/
│   └── page.tsx        # /papers (논문만)
├── feed.xml/
│   └── route.ts        # RSS 피드
└── sitemap.ts          # 사이트맵
```

**새로 추가된 컴포넌트:**
```
frontend/src/components/
├── Navigation.tsx      # 카테고리 탭 네비게이션
├── ArticleCard.tsx     # 기사 카드 컴포넌트
├── ThemeToggle.tsx     # 테마 토글 (기존)
└── ErrorBoundary.tsx   # 에러 바운더리 (기존)
```

---

## 2. 현재 프로젝트 구조

### 백엔드 구조
```
backend/
├── main.py                 # FastAPI 앱 (category 필터 지원)
├── models.py               # Article 모델 (category, source_type 포함)
├── schemas.py              # Pydantic 스키마
├── crud.py                 # DB 작업 (카테고리 필터링)
├── database.py             # DB 연결
├── config.py               # 설정 관리
├── collect_data.py         # 데이터 수집 파이프라인
├── scheduler.py            # 스케줄러
├── sources.json            # 데이터 소스 정의
├── collector/
│   ├── rss_collector.py    # RSS 수집
│   ├── pubmed_collector.py # PubMed 수집
│   └── scholar_collector.py # Google Scholar 수집
├── processor/
│   ├── summarizer.py       # AI 요약
│   └── relevance_filter.py # 관련성 필터
└── utils/
    ├── cache.py            # 캐싱
    └── retry.py            # 재시도 로직
```

### 프론트엔드 구조
```
frontend/src/
├── app/
│   ├── layout.tsx          # Root 레이아웃
│   ├── globals.css         # 전역 스타일 (탭, 뱃지 포함)
│   ├── page.tsx            # 홈 (전체 기사)
│   ├── news/page.tsx       # 뉴스 페이지
│   ├── papers/page.tsx     # 논문 페이지
│   ├── feed.xml/route.ts   # RSS 피드
│   └── sitemap.ts          # 사이트맵
├── components/
│   ├── Navigation.tsx      # 카테고리 탭
│   ├── ArticleCard.tsx     # 기사 카드
│   ├── ThemeToggle.tsx     # 테마 토글
│   └── ErrorBoundary.tsx   # 에러 바운더리
└── types.ts                # TypeScript 타입
```

---

## 3. 데이터 현황

### 카테고리별 분류
| 카테고리 | 개수 | 비율 |
|----------|------|------|
| 뉴스 (news) | 40 | 30% |
| 논문 (paper) | 94 | 70% |
| **합계** | **134** | 100% |

### 뉴스 소스
- Dermatology Times articles
- 의학신문 - 전체기사
- 청년의사 - 전체기사
- 뷰티경제 - 전체기사

### 논문 소스
- Journal of the American Academy of Dermatology (JAAD)
- Wiley: JEADV
- Wiley: Lasers in Surgery and Medicine
- Wiley: Journal of Cosmetic Dermatology
- PubMed | {저널명}
- Google Scholar

---

## 4. 남은 작업 (향후 계획)

### Phase 4: 추가 기능 개발 (선택사항)

#### 4.1 상세 페이지 구현
| 항목 | 우선순위 | 설명 |
|------|---------|------|
| /news/[id] | 중간 | 뉴스 상세 페이지 |
| /papers/[id] | 중간 | 논문 상세 페이지 |
| 관련 기사 추천 | 낮음 | 키워드 기반 관련 기사 |

#### 4.2 사용자 기능
| 항목 | 우선순위 | 설명 |
|------|---------|------|
| 북마크 기능 | 중간 | 기사 저장 (localStorage) |
| 읽음 표시 | 낮음 | 읽은 기사 체크 |
| 카테고리 선호 저장 | 낮음 | 사용자 선호 카테고리 기억 |

#### 4.3 SEO 및 피드 개선
| 항목 | 우선순위 | 설명 |
|------|---------|------|
| 카테고리별 RSS 피드 | 중간 | /news/feed.xml, /papers/feed.xml |
| 메타데이터 최적화 | 중간 | 각 페이지별 OG 태그 |
| sitemap 업데이트 | 낮음 | 동적 기사 URL 포함 |

#### 4.4 데이터 수집 개선
| 항목 | 우선순위 | 설명 |
|------|---------|------|
| 더 많은 뉴스 소스 | 높음 | 현재 뉴스 비율 30%로 낮음 |
| PubMed 수집량 증가 | 중간 | max_results 조정 |
| 중복 제거 강화 | 낮음 | 유사 기사 감지 |

#### 4.5 UI/UX 개선
| 항목 | 우선순위 | 설명 |
|------|---------|------|
| 무한 스크롤 | 중간 | "더 보기" 버튼 대체 |
| 카드 애니메이션 | 낮음 | 로딩/전환 효과 |
| 반응형 개선 | 중간 | 태블릿/모바일 최적화 |

---

## 5. 기술 부채 및 개선 필요 사항

### 코드 품질
| 항목 | 상태 | 개선 방안 |
|------|------|---------|
| 페이지 컴포넌트 중복 | ⚠️ | 공통 훅/컴포넌트 추출 |
| 타입 안전성 | ✅ | TypeScript 적용 완료 |
| 에러 처리 | ✅ | ErrorBoundary 적용 완료 |
| 테스트 부재 | ⚠️ | 단위/통합 테스트 필요 |

### 성능
| 항목 | 상태 | 개선 방안 |
|------|------|---------|
| API 캐싱 | ✅ | 5분 TTL 캐싱 적용 |
| DB 인덱스 | ✅ | category, published_date 인덱스 |
| 이미지 최적화 | N/A | 현재 이미지 없음 |
| 번들 크기 | ⚠️ | 코드 스플리팅 검토 필요 |

### 보안
| 항목 | 상태 | 비고 |
|------|------|------|
| CORS 설정 | ✅ | localhost:3000 허용 |
| SQL Injection | ✅ | SQLAlchemy ORM 사용 |
| XSS 방지 | ✅ | React 자동 이스케이프 |
| Rate Limiting | ⚠️ | 미적용, 필요 시 추가 |

---

## 6. 배포 체크리스트

### 프로덕션 배포 전 확인 사항
- [ ] 환경 변수 설정 (OPENAI_API_KEY, DATABASE_URL 등)
- [ ] CORS 설정 업데이트 (프로덕션 도메인)
- [ ] HTTPS 설정
- [ ] 데이터베이스 백업 전략
- [ ] 에러 모니터링 (Sentry 등)
- [ ] 로깅 설정
- [ ] CI/CD 파이프라인

---

## 7. 요약

### 완료된 핵심 기능
1. ✅ **카테고리 시스템**: 뉴스/논문 자동 분류
2. ✅ **별도 페이지**: /news, /papers 라우트
3. ✅ **API 필터링**: category 파라미터로 서버사이드 필터링
4. ✅ **UI 컴포넌트**: Navigation 탭, ArticleCard 카드
5. ✅ **스타일링**: 카테고리 뱃지, 반응형 탭

### 즉시 사용 가능한 기능
- 전체 기사 조회 (`/`)
- 뉴스만 조회 (`/news`)
- 논문만 조회 (`/papers`)
- 검색 및 필터링
- 다크/라이트 테마

### 권장 다음 단계
1. **데이터 수집 실행** - 더 많은 뉴스/논문 확보
2. **카테고리별 RSS 피드** - SEO 및 구독 기능
3. **상세 페이지** - 개별 기사 페이지

---

## 문서 정보

| 항목 | 내용 |
|------|------|
| 프로젝트 | MDinfo (Derma-Insight) |
| 기술 스택 | Next.js 16 / React 19 / FastAPI / SQLite |
| 분석 문서 | docs/NEWS_PAPER_SEPARATION_ANALYSIS.md |
| 구현 현황 | docs/IMPLEMENTATION_STATUS.md (본 문서) |

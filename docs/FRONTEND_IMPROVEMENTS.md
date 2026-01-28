# Frontend 개선 사항 체크리스트

이 문서는 MDinfo 프론트엔드 코드 분석 결과 발견된 개선 사항을 정리한 것입니다.

**분석 일자**: 2026-01-28
**총 개선 항목**: 64개
**진행 상황**: 45 / 64 완료

---

## 목차

1. [Critical 이슈 (즉시 수정 필요)](#1-critical-이슈-즉시-수정-필요)
2. [코드 품질 이슈](#2-코드-품질-이슈)
3. [TypeScript 타입 안전성](#3-typescript-타입-안전성)
4. [접근성 (a11y) 이슈](#4-접근성-a11y-이슈)
5. [성능 최적화](#5-성능-최적화)
6. [에러 처리](#6-에러-처리)
7. [보안 이슈](#7-보안-이슈)
8. [SEO 개선](#8-seo-개선)
9. [UX 기능 추가](#9-ux-기능-추가)
10. [코드 구조 및 유지보수성](#10-코드-구조-및-유지보수성)
11. [Best Practices](#11-best-practices)

---

## 1. Critical 이슈 (즉시 수정 필요)

### 1.1 API URL 하드코딩
- [x] **환경변수로 API URL 분리** ✅
  - 파일: `src/app/page.tsx:6`
  - 문제: `http://localhost:8000/articles/` 하드코딩
  - 해결: `process.env.NEXT_PUBLIC_API_URL` 사용
  - 추가 작업: `.env.local` 및 `.env.example` 파일 생성

### 1.2 에러 상태 UI 없음
- [x] **에러 발생 시 사용자에게 표시되는 UI 추가** ✅
  - 파일: `src/app/page.tsx:35-45`
  - 문제: `catch` 블록에서 `console.error`만 호출
  - 해결: 에러 상태 변수 추가 및 에러 UI 컴포넌트 렌더링, 다시 시도 버튼 포함

### 1.3 언어 속성 불일치
- [x] **HTML lang 속성을 "ko"로 변경** ✅
  - 파일: `src/app/layout.tsx:26`
  - 문제: `lang="en"`이지만 콘텐츠는 한국어
  - 해결: `<html lang="ko">` 로 수정

### 1.4 메타 태그 미설정
- [x] **프로젝트에 맞는 title/description 설정** ✅
  - 파일: `src/app/layout.tsx:15-18`
  - 문제: "Create Next App" 기본값 사용 중
  - 해결:
    - title: "Derma-Insight | 피부과 연구 뉴스"
    - description: "AI가 요약한 최신 피부과/미용 연구 논문과 업계 뉴스"

---

## 2. 코드 품질 이슈

### 2.1 인라인 스타일 사용
- [x] **인라인 스타일을 CSS 클래스로 이동** ✅
  - 파일: `src/app/page.tsx`, `src/app/globals.css`
  - 문제: 여러 곳에 인라인 `style={{}}` 객체 사용
  - 해결: `.original-title`, `.summary-box`, `.summary-label`, `.keywords-container` 클래스 생성

### 2.2 빈 상태 UI 없음
- [x] **데이터가 없을 때 안내 메시지 표시** ✅
  - 파일: `src/app/page.tsx:82-86`
  - 문제: `articles` 배열이 비어있으면 빈 그리드만 표시
  - 해결: `.empty-state` UI 추가 및 조건 분기

### 2.3 로딩 스켈레톤 없음
- [x] **로딩 중 스켈레톤 UI 구현** ✅
  - 파일: `src/app/page.tsx:35-58`, `src/app/globals.css`
  - 문제: 단순 "Loading..." 텍스트
  - 해결: 카드 레이아웃 형태의 스켈레톤 컴포넌트 및 shimmer 애니메이션 추가

### 2.4 미사용 CSS 클래스
- [x] **사용하지 않는 CSS 클래스 정리** ✅
  - 파일: `src/app/globals.css`
  - 문제: `.tag`, `.source` 클래스 정의되어 있으나 미사용
  - 해결: 삭제 완료

### 2.5 미사용 CSS Module 파일
- [x] **page.module.css 파일 정리** ✅
  - 파일: `src/app/page.module.css`
  - 문제: 파일 존재하나 import되지 않음
  - 해결: 파일 삭제

---

## 3. TypeScript 타입 안전성

### 3.1 API 응답 타입 미검증
- [x] **fetch 응답에 타입 검증 추가** ✅
  - 파일: `src/types.ts`, `src/app/page.tsx:21-24`
  - 문제: `res.json()`이 `any` 타입 반환
  - 해결: `isArticleArray()` 타입 가드 함수 생성 및 런타임 검증

### 3.2 옵셔널 필드 미처리
- [x] **keywords 필드 null/undefined 체크** ✅
  - 파일: `src/app/page.tsx:113`
  - 문제: `article.keywords.split(',')` - keywords가 없으면 에러
  - 해결: `article.keywords?.split(',')` 옵셔널 체이닝 사용

### 3.3 타입 정의 불일치
- [x] **is_read 필드를 옵셔널로 변경** ✅
  - 파일: `src/types.ts:11`
  - 문제: `is_read: boolean`이 필수지만 백엔드에서 미제공
  - 해결: `is_read?: boolean` 옵셔널로 변경

### 3.4 catch 블록 error 타입
- [x] **error 변수 타입 처리** ✅
  - 파일: `src/app/page.tsx:22-23`
  - 문제: `catch(error)` - error가 `unknown` 타입
  - 해결: `error instanceof Error` 타입 가드 사용

### 3.5 빈 문자열 keywords 처리
- [x] **빈 keywords 문자열 처리** ✅
  - 파일: `src/app/page.tsx:106`
  - 문제: `"".split(',')` → `['']` 빈 태그 렌더링
  - 해결: `.filter(Boolean)` 추가

---

## 4. 접근성 (a11y) 이슈

### 4.1 색상 대비 부족
- [x] **날짜 텍스트 색상 대비 개선** ✅
  - 파일: `src/app/globals.css:5`
  - 문제: `#666` 색상이 WCAG AA 기준 미달 (4.5:1 필요)
  - 해결: `--secondary: #595959`로 변경

### 4.2 헤딩 계층 구조 오류
- [x] **h1 → h2 → h3 순서 맞추기** ✅
  - 파일: `src/app/page.tsx`
  - 문제: `<h1>` 다음에 바로 `<h3>` 사용 (h2 누락)
  - 해결: 아티클 제목을 `<h2>`로 변경, CSS로 크기 조정

### 4.3 키보드 포커스 스타일 없음
- [x] **:focus 스타일 추가** ✅
  - 파일: `src/app/globals.css`
  - 문제: `.keyword-tag`에 `:hover`만 있고 `:focus` 없음
  - 해결: `a:focus-visible`, `button:focus-visible`, `.keyword-tag:focus-visible` 스타일 추가

### 4.4 이모지 대체 텍스트 없음
- [x] **이모지에 aria-label 추가** ✅
  - 파일: `src/app/page.tsx:119`
  - 문제: 💡 이모지가 의미를 전달하지만 스크린 리더 접근 불가
  - 해결: `<span role="img" aria-label="전구 아이콘">💡</span>`

### 4.5 링크 접근성 개선
- [x] **외부 링크임을 명시** ✅
  - 파일: `src/app/page.tsx:105-110`, `src/app/globals.css`
  - 문제: 외부 링크로 이동함을 스크린 리더 사용자가 알 수 없음
  - 해결: `.external-link::after { content: " ↗" }` 아이콘 + `.sr-only` 텍스트 "(새 탭에서 열림)"

### 4.6 Skip to content 링크 없음
- [x] **본문 바로가기 링크 추가** ✅
  - 파일: `src/app/layout.tsx:28-30`, `src/app/globals.css`
  - 문제: 키보드 사용자가 헤더를 건너뛸 수 없음
  - 해결: `.skip-link` 추가, 포커스 시 보이도록 구현

### 4.7 포커스 관리
- [x] **데이터 로드 후 포커스 이동** ✅
  - 파일: `src/app/page.tsx`
  - 문제: 로딩 완료 후 포커스가 적절히 이동하지 않음
  - 해결: `id="main-content"` 추가, skip link와 연동, 로딩 스켈레톤에 `role="status"` 추가

---

## 5. 성능 최적화

### 5.1 페이지네이션 UI 없음
- [x] **페이지네이션 또는 무한 스크롤 구현** ✅
  - 파일: `src/app/page.tsx`
  - 문제: 100개 아티클을 한 번에 로드/렌더링
  - 해결: "더 보기" 버튼으로 12개씩 로드, 백엔드 `skip/limit` 활용

### 5.2 데이터 캐싱 없음
- [ ] **SWR 또는 React Query 도입** (추후 검토)
  - 파일: `src/app/page.tsx`
  - 문제: 매 요청마다 전체 데이터 fetch
  - 해결: 클라이언트 캐싱 라이브러리 도입 필요
  - 참고: 페이지네이션 적용으로 초기 로드량 감소 (100개 → 12개)

### 5.3 Server Component 미활용
- [ ] **서버 컴포넌트로 전환 검토** (추후 검토)
  - 파일: `src/app/page.tsx:1`
  - 문제: `'use client'`로 전체 클라이언트 렌더링
  - 해결: 데이터 fetch를 서버 컴포넌트로, 인터랙션만 클라이언트로
  - 참고: 현재 페이지네이션 상태 관리로 인해 클라이언트 컴포넌트 필요

### 5.4 Preconnect 미설정
- [x] **API 서버 preconnect 추가** ✅
  - 파일: `src/app/layout.tsx:29-31`
  - 문제: API 연결 지연
  - 해결: `<link rel="preconnect">` 및 `<link rel="dns-prefetch">` 추가

### 5.5 Virtual Scrolling 미적용
- [ ] **대량 데이터 가상 스크롤 적용** (추후 검토)
  - 파일: `src/app/page.tsx`
  - 문제: 100개 이상 아티클 시 DOM 노드 과다
  - 해결: react-window 또는 @tanstack/virtual 도입
  - 참고: 페이지네이션으로 한 번에 12개만 렌더링하여 문제 완화

---

## 6. 에러 처리

### 6.1 네트워크 에러 재시도 없음
- [x] **재시도 버튼 추가** ✅
  - 파일: `src/app/page.tsx`
  - 문제: 에러 발생 시 사용자가 수동 새로고침 필요
  - 해결: 에러 UI에 "다시 시도" 버튼 추가

### 6.2 Timeout 처리 없음
- [x] **fetch에 timeout 추가** ✅
  - 파일: `src/app/page.tsx:9, 42-44`
  - 문제: 백엔드 응답 없으면 무한 대기
  - 해결: `AbortController`로 10초 timeout 구현

### 6.3 Error Boundary 없음
- [x] **React Error Boundary 추가** ✅
  - 파일: `src/components/ErrorBoundary.tsx`, `src/app/layout.tsx`
  - 문제: 렌더링 에러 시 전체 페이지 크래시
  - 해결: ErrorBoundary 컴포넌트 생성 및 layout에 적용

### 6.4 필수 데이터 검증 없음
- [x] **아티클 필수 필드 검증** ✅
  - 파일: `src/app/page.tsx:23-25, 63`
  - 문제: `article.title`, `article.url` 없으면 렌더링 오류
  - 해결: `isValidArticle()` 함수로 필수 필드(id, title, url, source) 검증

### 6.5 CORS 에러 안내 없음
- [x] **CORS 에러 발생 시 친화적 메시지** ✅
  - 파일: `src/app/page.tsx:11-21`
  - 문제: CORS 에러 시 사용자가 원인 파악 불가
  - 해결: `getErrorMessage()` 함수로 에러 타입별 안내 메시지 (네트워크, 타임아웃, CORS 등)

---

## 7. 보안 이슈

### 7.1 CSP 헤더 미설정
- [x] **Content-Security-Policy 헤더 추가** ✅
  - 파일: `next.config.ts`
  - 문제: XSS 공격에 취약
  - 해결: security headers 설정 (CSP, X-XSS-Protection, X-Frame-Options 등)

### 7.2 API 응답 무검증
- [x] **API 응답 데이터 검증** ✅
  - 파일: `src/app/page.tsx`, `src/types.ts`
  - 문제: 백엔드 응답을 그대로 신뢰
  - 해결: `isArticleArray()` 타입 가드 + `isValidArticle()` 필수 필드 검증
  - 참고: HTML을 직접 렌더링하지 않으므로 DOMPurify 불필요

### 7.3 환경변수 노출 위험
- [x] **.env.example 파일 생성** ✅
  - 파일: `.env.example`
  - 문제: 필요한 환경변수 문서화 안됨
  - 해결: 예시 환경변수 파일 생성

### 7.4 외부 링크 보안
- [x] **rel="noopener noreferrer" 확인** ✅
  - 파일: `src/app/page.tsx`
  - 상태: 정상 적용되어 있음

### 7.5 의존성 취약점 점검
- [x] **npm audit 실행 및 취약점 수정** ✅
  - 파일: `package.json`
  - 결과: 취약점 0개 (found 0 vulnerabilities)

---

## 8. SEO 개선

### 8.1 Open Graph 태그 없음
- [x] **소셜 미디어 미리보기 메타 태그 추가** ✅
  - 파일: `src/app/layout.tsx:32-47`
  - 해결: `og:title`, `og:description`, `og:image`, `og:locale` 등 추가

### 8.2 Twitter Card 없음
- [x] **Twitter 공유용 메타 태그 추가** ✅
  - 파일: `src/app/layout.tsx:48-53`
  - 해결: `twitter:card`, `twitter:title`, `twitter:description`, `twitter:images` 추가

### 8.3 구조화 데이터 없음
- [x] **JSON-LD Schema.org 마크업 추가** ✅
  - 파일: `src/app/layout.tsx:72-83`
  - 해결: WebSite 스키마 추가 (JSON-LD)

### 8.4 sitemap.xml 없음
- [x] **사이트맵 생성** ✅
  - 파일: `src/app/sitemap.ts`
  - 해결: Next.js 동적 sitemap 생성

### 8.5 robots.txt 없음
- [x] **robots.txt 파일 추가** ✅
  - 파일: `public/robots.txt`
  - 해결: 크롤링 허용, sitemap 링크 포함

### 8.6 Canonical URL 없음
- [x] **canonical 링크 태그 추가** ✅
  - 파일: `src/app/layout.tsx:29-31`
  - 해결: `metadataBase` + `alternates.canonical` 설정

### 8.7 Favicon 최적화
- [ ] **다양한 크기의 favicon 제공** (이미지 준비 필요)
  - 파일: `public/`
  - 해결: metadata.icons에 설정 완료, 실제 이미지 파일 준비 필요
  - 필요 파일: `favicon.ico`, `favicon-16x16.png`, `apple-touch-icon.png`, `og-image.png`

### 8.8 RSS 피드 제공
- [x] **RSS 피드 엔드포인트 추가** ✅
  - 파일: `src/app/feed.xml/route.ts`
  - 해결: `/feed.xml` 경로로 RSS 2.0 피드 제공, 1시간 캐시

---

## 9. UX 기능 추가

### 9.1 검색 기능 없음
- [x] **아티클 검색 기능 구현** ✅
  - 파일: `src/app/page.tsx`
  - 해결: 제목, 요약, 키워드 실시간 검색 UI

### 9.2 필터 기능 없음
- [x] **소스별 필터 구현** ✅
  - 파일: `src/app/page.tsx`
  - 해결: 소스 선택 드롭다운 필터

### 9.3 정렬 옵션 없음
- [x] **정렬 기능 추가** ✅
  - 파일: `src/app/page.tsx`
  - 해결: 최신순, 오래된순, 소스순 정렬 옵션

### 9.4 다크모드 토글 없음
- [x] **수동 다크모드 전환 버튼 추가** ✅
  - 파일: `src/components/ThemeToggle.tsx`, `src/app/globals.css`
  - 해결: 라이트/다크/시스템 3단계 토글, localStorage 저장

### 9.5 북마크/즐겨찾기 없음
- [ ] **아티클 저장 기능 구현** (추후 검토)
  - 해결: localStorage 또는 백엔드 연동 필요

### 9.6 공유 버튼 없음
- [x] **링크 복사 버튼 추가** ✅
  - 파일: `src/app/page.tsx`
  - 해결: 각 카드에 🔗 버튼으로 URL 클립보드 복사

### 9.7 아티클 상세 페이지 없음
- [ ] **개별 아티클 페이지 생성** (추후 검토)
  - 해결: `/articles/[id]` 동적 라우트 추가 필요

---

## 10. 코드 구조 및 유지보수성

### 10.1 컴포넌트 미분리
- [ ] **ArticleCard 컴포넌트 추출**
  - 파일: `src/app/page.tsx`
  - 해결: `src/components/ArticleCard.tsx` 생성

- [ ] **Header 컴포넌트 추출**
  - 해결: `src/components/Header.tsx` 생성

- [ ] **ArticleGrid 컴포넌트 추출**
  - 해결: `src/components/ArticleGrid.tsx` 생성

- [ ] **LoadingState 컴포넌트 추출**
  - 해결: `src/components/LoadingState.tsx` 생성

- [ ] **ErrorState 컴포넌트 추출**
  - 해결: `src/components/ErrorState.tsx` 생성

- [ ] **EmptyState 컴포넌트 추출**
  - 해결: `src/components/EmptyState.tsx` 생성

### 10.2 커스텀 훅 없음
- [ ] **useArticles 훅 생성**
  - 해결: `src/hooks/useArticles.ts` - 데이터 fetch 로직 분리

### 10.3 유틸리티 함수 없음
- [ ] **날짜 포맷 유틸리티 생성**
  - 해결: `src/utils/dateFormatter.ts`

- [ ] **API 클라이언트 유틸리티 생성**
  - 해결: `src/utils/api.ts`

### 10.4 상수 파일 없음
- [ ] **상수 파일 생성**
  - 해결: `src/constants.ts` - API URL, 매직 넘버 등

### 10.5 스타일링 방식 혼재
- [ ] **일관된 스타일링 방식 적용**
  - 문제: CSS Module, Global CSS, 인라인 스타일 혼용
  - 해결: 하나의 방식으로 통일 (권장: CSS Module 또는 Tailwind)

### 10.6 README 미업데이트
- [ ] **프로젝트별 README 작성**
  - 파일: `frontend/README.md`
  - 문제: Next.js 템플릿 기본 내용
  - 해결: 프로젝트 설명, 설치 방법, 환경변수 등 문서화

---

## 11. Best Practices

### 11.1 package.json 스크립트 부족
- [ ] **추가 npm 스크립트 정의**
  - 파일: `package.json`
  - 추가할 스크립트:
    - `"typecheck": "tsc --noEmit"`
    - `"lint:fix": "next lint --fix"`
    - `"format": "prettier --write ."`

### 11.2 Prettier 미설정
- [ ] **Prettier 설정 추가**
  - 해결: `.prettierrc` 파일 생성

### 11.3 Git Hooks 미설정
- [ ] **Husky + lint-staged 설정**
  - 해결: 커밋 전 lint/typecheck 자동 실행

### 11.4 테스트 없음
- [ ] **Jest/Testing Library 설정**
  - 해결: 컴포넌트 유닛 테스트 추가

### 11.5 console.log 프로덕션 노출
- [x] **console 문 제거 또는 조건부 실행** ✅
  - 파일: `src/app/page.tsx`
  - 해결: console.error 제거, 에러는 UI로 표시

### 11.6 noUncheckedIndexedAccess 미설정
- [ ] **TypeScript strict 옵션 강화**
  - 파일: `tsconfig.json`
  - 해결: `"noUncheckedIndexedAccess": true` 추가

---

## 변경 이력

| 날짜 | 작업 내용 | 완료 항목 |
|------|----------|----------|
| 2026-01-28 | 문서 최초 작성 | - |
| 2026-01-28 | Critical 이슈 수정 | 1.1, 1.2, 1.3, 1.4, 3.4, 6.1, 7.3, 11.5 |
| 2026-01-28 | 코드 품질 이슈 수정 | 2.1, 2.2, 2.3, 2.4, 2.5, 3.5 |
| 2026-01-28 | TypeScript 타입 안전성 수정 | 3.1, 3.2, 3.3 |
| 2026-01-28 | 접근성(a11y) 이슈 수정 | 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7 |
| 2026-01-28 | 성능 최적화 수정 | 5.1, 5.4 (5.2, 5.3, 5.5는 추후 검토) |
| 2026-01-28 | 에러 처리 수정 | 6.2, 6.3, 6.4, 6.5 |
| 2026-01-28 | 보안 이슈 수정 | 7.1, 7.2, 7.5 |
| 2026-01-28 | SEO 개선 | 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.8 (8.7 이미지 준비 필요) |
| 2026-01-28 | UX 기능 추가 | 9.1, 9.2, 9.3, 9.4, 9.6 (9.5, 9.7 추후 검토) |

---

## 참고 사항

- 우선순위: Critical > 코드 품질 > TypeScript > 접근성 > 성능 > 나머지
- 각 항목 완료 시 `- [ ]`를 `- [x]`로 변경
- 관련 커밋이나 PR 번호를 변경 이력에 기록

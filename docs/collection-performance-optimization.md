# 데이터 수집 속도 최적화

## 병목 분석

현재 파이프라인은 **모든 작업이 순차 실행**되어 전체 ~236초 소요.

| 단계 | 소요 시간 | 비중 | 원인 |
|------|-----------|------|------|
| OpenAI 요약 (65건 x 3초) | ~195초 | **83%** | 1건씩 순차 API 호출 |
| Scholar 수집 (10키워드 x 2초) | ~20초 | 8% | `time.sleep(2)` per keyword |
| PubMed 수집 (10쿼리 x 1초) | ~10초 | 4% | `time.sleep(1)` per query |
| RSS 수집 (4피드 x 1초) | ~4초 | 2% | `time.sleep(1)` per feed |
| DB 작업 | ~7초 | 3% | 건별 dedup 쿼리 + insert |
| **합계** | **~236초** | | |

## 최적화 전략

### 1. 3단계 분리 (collect_data.py)

기존 구조: 수집 -> 요약 -> 저장을 아티클 1건마다 반복
변경 구조:
1. **수집 단계**: RSS -> PubMed -> Scholar 순차 수집 후 DB 중복 필터링하여 신규 아티클 목록 확보
2. **요약 단계**: `ThreadPoolExecutor(max_workers=5)`로 OpenAI 호출 병렬화
3. **저장 단계**: 요약 완료된 아티클을 순차적으로 DB에 저장

### 2. 병렬 요약 (ThreadPoolExecutor)

- `concurrent.futures.ThreadPoolExecutor(max_workers=5)` 사용
- OpenAI `httpx` 클라이언트는 thread-safe -> 별도 조치 불필요
- SQLAlchemy Session은 thread-safe하지 않으므로 메인 스레드에서만 DB 접근

## 수정 파일

| 파일 | 변경 |
|------|------|
| `backend/collect_data.py` | 3단계 분리 + ThreadPoolExecutor 도입 |

## 예상 결과

| | 변경 전 | 변경 후 |
|---|---------|---------|
| 요약 단계 | ~195초 (순차) | ~40초 (5병렬) |
| 수집/DB 단계 | ~41초 | ~41초 (변경 없음) |
| **합계** | **~236초** | **~81초 (약 66% 단축)** |

---

## Google Scholar CAPTCHA 무한 대기 해결

### 문제

`scholarly` 라이브러리는 Google Scholar에서 HTTP 429(CAPTCHA)를 받으면 내부 `_handle_captcha2`에서 최대 604,800초(7일) 동안 재시도 루프에 진입한다. 브라우저가 없으면 CAPTCHA를 풀 수 없어 전체 수집 파이프라인이 멈춘다.

### 해결: 2단계 데몬 스레드 타임아웃

`threading.Thread(daemon=True)` + `thread.join(timeout)`으로 블로킹 호출에 타임아웃을 건다. 데몬 스레드는 프로세스 종료 시 자동 정리되므로 리소스 누수가 없다.

| 레이어 | 위치 | 타임아웃 | 역할 |
|--------|------|----------|------|
| **내부** | `scholar_collector.py` 키워드별 | 15초 | CAPTCHA 감지 시 해당 키워드 스킵 + 나머지 즉시 중단 |
| **외부** | `collect_data.py` Scholar 전체 | 60초 | 내부 타임아웃 실패 시 안전망 |

### CAPTCHA 발생 시 흐름 (키워드 3에서 발생한 경우)

```
collect_data.py (60초 안전망)
  └─ scholar_collector.search_articles()
       ├─ 키워드 1: 성공 (5초)
       ├─ 키워드 2: 성공 (5초)
       └─ 키워드 3: 타임아웃 (15초) → break → 키워드 1-2 결과만 반환
→ RSS + PubMed 결과와 합쳐서 요약/저장 정상 진행
```

### 수정 파일

| 파일 | 변경 |
|------|------|
| `backend/collector/scholar_collector.py` | `_run_with_timeout` 헬퍼 + 키워드별 15초 타임아웃 |
| `backend/collect_data.py` | Scholar 수집 블록을 데몬 스레드 + 60초 타임아웃으로 래핑 |

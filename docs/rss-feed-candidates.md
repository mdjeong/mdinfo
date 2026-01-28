# RSS 피드 후보 목록

> 검증일: 2026-01-28

## 현재 사용 중인 피드

`backend/sources.json` 기준 (8개):

### 해외 피드 (5개)

| 피드명 | URL | 수집 | 상태 |
|--------|-----|------|------|
| JAAD | `https://www.jaad.org/current.rss` | 591개 | 정상 |
| JEADV | `https://onlinelibrary.wiley.com/feed/14683083/most-recent` | 125개 | 정상 |
| Dermatology Times | `https://www.dermatologytimes.com/rss` | 30개 | 정상 (CDATA 전처리 적용) |
| Lasers in Surgery and Medicine | `https://onlinelibrary.wiley.com/feed/10969101/most-recent` | 20개 | 정상 |
| Journal of Cosmetic Dermatology | `https://onlinelibrary.wiley.com/feed/14732165/most-recent` | 3개 | 정상 |

### 국내 피드 (3개)

| 피드명 | URL | 수집 | 상태 |
|--------|-----|------|------|
| 의학신문 | `http://www.bosa.co.kr/rss/allArticle.xml` | 50개 | 정상 |
| 청년의사 | `http://www.docdocdoc.co.kr/rss/allArticle.xml` | 50개 | 정상 |
| 뷰티경제 | `http://www.thebk.co.kr/rss/allArticle.xml` | 50개 | 정상 |

**총 919개 아티클** 수집 가능.

### 제거된 피드

| 피드명 | URL | 제거 사유 |
|--------|-----|-----------|
| MDedge Dermatology | `mdedge.com/dermatology/rss` | bozo 에러 (XML 파싱 오류) |
| Dermatologic Surgery (LWW) | `journals.lww.com/.../feed.aspx` | RSS 대신 HTML 반환 (서비스 중단) |
| Plastic and Reconstructive Surgery (LWW) | `journals.lww.com/.../feed.aspx` | RSS 대신 HTML 반환 (서비스 중단) |
| Aesthetic Plastic Surgery (Springer) | `link.springer.com/search.rss?...` | 불안정 (빈 응답/타임아웃) |

---

## 검증 완료된 대체 후보 피드

아래 피드들은 2026-01-28 기준 정상 동작 확인됨.

### 미용/성형 특화 (Aesthetics-focused)

| 피드명 | URL | 엔트리 수 | 비고 |
|--------|-----|----------|------|
| **Journal of Cosmetic Dermatology** | `https://onlinelibrary.wiley.com/feed/14732165/most-recent` | 3 | Wiley, 미용피부 전문 |
| **Aesthetic Plastic Surgery** | `https://link.springer.com/search.rss?search-within=Journal&facet-journal-id=266&query=` | 20 | Springer, 성형외과 |
| **Lasers in Surgery and Medicine** | `https://onlinelibrary.wiley.com/feed/10969101/most-recent` | 20 | Wiley, 레이저/에너지 기기 |
| **Skin Research and Technology** | `https://onlinelibrary.wiley.com/feed/16000846/most-recent` | 19 | Wiley, 피부 기술 연구 |

### 일반 피부과 저널

| 피드명 | URL | 엔트리 수 | 비고 |
|--------|-----|----------|------|
| **JAAD** (J Am Acad Dermatol) | `https://www.jaad.org/current.rss` | 591 | Elsevier, 미국피부과학회지 |
| **JEADV** (J Eur Acad Dermatol Venereol) | `https://onlinelibrary.wiley.com/feed/14683083/most-recent` | 125 | Wiley, 유럽피부과학회지 |
| **International J of Dermatology** | `https://onlinelibrary.wiley.com/feed/13654632/most-recent` | 111 | Wiley, 국제피부과학회지 |
| **J Dermatological Treatment** | `https://www.tandfonline.com/feed/rss/ijdt20` | 20 | Taylor & Francis, 치료 중심 |

---

## 동작하지 않는 피드

| 피드명 | URL | 상태 |
|--------|-----|------|
| British Journal of Dermatology | `academic.oup.com/bjd/rss` | 404 |
| Aesthetic Surgery Journal | `academic.oup.com/asj/rss` | 404 |
| JAMA Dermatology | `jamanetwork.com/rss/...` | 일반 JAMA 피드만 제공, 피부과 전용 없음 |
| Dermatologic Therapy (Wiley) | `onlinelibrary.wiley.com/feed/15298019/...` | 0 엔트리 |
| Dermatology Research & Practice | `onlinelibrary.wiley.com/feed/3029/...` | 0 엔트리 |
| Clinical Cosmetic Investigational Derm | `dovepress.com/...` | 404 |

---

## 추가 고려 가능한 해외 피드

| 피드명 | URL | 비고 |
|--------|-----|------|
| International J of Dermatology | `https://onlinelibrary.wiley.com/feed/13654632/most-recent` | 111개, Wiley |
| J Dermatological Treatment | `https://www.tandfonline.com/feed/rss/ijdt20` | 20개, Taylor & Francis |
| Skin Research and Technology | `https://onlinelibrary.wiley.com/feed/16000846/most-recent` | 19개, Wiley |

---

## 국내 피드

### 동작 확인된 국내 피드

| 매체명 | URL | 엔트리 | 분야 |
|--------|-----|--------|------|
| **의학신문** | `http://www.bosa.co.kr/rss/allArticle.xml` | 50개 | 의료 전반 |
| **청년의사** | `http://www.docdocdoc.co.kr/rss/allArticle.xml` | 50개 | 의료 전반 |
| **의협신문** | `https://www.doctorsnews.co.kr/rss/allArticle.xml` | 50개 | 의료정책/의사협회 |
| **뷰티경제** | `http://www.thebk.co.kr/rss/allArticle.xml` | 50개 | 화장품/뷰티 산업 |

### 동작하지 않는 국내 피드

| 매체명 | URL | 상태 |
|--------|-----|------|
| 메디게이트뉴스 | `medigatenews.com/rss` | RSS 미제공 (HTML 반환) |
| 메디컬투데이 | `mdtoday.co.kr/rss/...` | 404 |
| 메디칼타임즈 | `medicaltimes.com/rss/...` | 404 |
| 코스인 | `cosinkorea.com/rss/...` | RSS 미제공 |
| CMN 화장품신문 | `cmn.co.kr/rss/...` | 404 |
| 뷰티누리 | `beautynury.com/rss/...` | SSL 오류 |
| 코스모닝 | `cosmorning.com/rss/...` | RSS 미제공 |

---

## 참고 자료

- [Feedspot Top 100 Dermatology RSS Feeds](https://rss.feedspot.com/dermatology_rss_feeds/)
- [Feedspot Top 100 Skin Care RSS Feeds](https://rss.feedspot.com/skin_care_rss_feeds/)

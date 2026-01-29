"""
의료 관련성 필터 모듈
OpenAI gpt-4o-mini를 사용하여 RSS 뉴스 기사가 피부과/미용 분야와 관련이 있는지 판단
"""

import logging
from typing import Dict, Tuple
from openai import OpenAI

logger = logging.getLogger(__name__)


class MedicalRelevanceFilter:
    """의료 관련성을 판단하는 필터 클래스"""

    # 영어 의료 키워드
    MEDICAL_KEYWORDS_EN = {
        'dermatology', 'skin', 'aesthetics', 'cosmetic', 'beauty', 'laser',
        'botox', 'botulinum', 'filler', 'injection', 'rejuvenation', 'wrinkle',
        'acne', 'rosacea', 'eczema', 'psoriasis', 'melanoma', 'carcinoma',
        'dermato', 'facial', 'peeling', 'microneedling', 'hifu', 'ultrasound',
        'radiofrequency', 'plasma', 'stem cell', 'exosome', 'regenerative',
        'anti-aging', 'pigmentation', 'melasma', 'vitiligo', 'alopecia',
        'hair loss', 'scalp', 'wound', 'scar', 'keloid', 'collagen',
        'hyaluronic', 'retinol', 'peptide', 'clinical trial', 'fda approval',
        'medical device', 'therapy', 'treatment', 'procedure', 'surgery',
        'plastic surgery', 'cosmetic surgery', 'aesthetic medicine'
    }

    # 한국어 의료 키워드
    MEDICAL_KEYWORDS_KR = {
        '피부과', '피부', '미용', '성형', '주름', '보톡스', '필러', '레이저',
        '리프팅', '엑소좀', '줄기세포', '재생', '안티에이징', '노화', '기미',
        '미백', '여드름', '아토피', '건선', '피부암', '흑색종', '탈모',
        '두피', '흉터', '콜라겐', '히알루론산', '레티놀', '펩타이드',
        '임상시험', '식약처', '의료기기', '치료', '시술', '수술', '성형외과',
        '피부미용', '메디컬', '클리닉', '병원', '환자', '진료', '처방',
        '약물', '연구', '논문', '학회', '컨퍼런스'
    }

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API 키
            model: 사용할 모델 (기본값: gpt-4o-mini)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"MedicalRelevanceFilter 초기화 완료 (model={model})")

    def _quick_keyword_check(self, title: str, text: str) -> bool:
        """
        키워드 기반 사전검사
        명백한 의료 콘텐츠는 즉시 통과

        Args:
            title: 기사 제목
            text: 기사 본문 또는 요약

        Returns:
            True if 의료 키워드 발견, False otherwise
        """
        content = f"{title} {text}".lower()

        # 영어 키워드 체크
        for keyword in self.MEDICAL_KEYWORDS_EN:
            if keyword in content:
                return True

        # 한국어 키워드 체크
        for keyword in self.MEDICAL_KEYWORDS_KR:
            if keyword in content:
                return True

        return False

    def _call_filter_api(self, title: str, text: str, source: str) -> Dict:
        """
        OpenAI API를 호출하여 의료 관련성 판단

        Args:
            title: 기사 제목
            text: 기사 본문 또는 요약
            source: 뉴스 소스명

        Returns:
            Dict with keys: is_relevant (bool), confidence (float), category (str), reason (str)
        """
        prompt = f"""다음 뉴스 기사가 피부과, 미용의학, 성형외과, 의료기기 분야와 관련이 있는지 판단해주세요.

뉴스 소스: {source}
제목: {title}
내용: {text[:500]}

관련이 있는 경우:
- 피부 질환, 피부 치료, 피부 연구
- 미용 시술 (보톡스, 필러, 레이저, 리프팅 등)
- 성형외과 수술 및 연구
- 의료기기 개발, 승인, 임상시험
- 화장품 연구 (의료/과학적 내용)
- 피부과/성형외과 학회, 컨퍼런스

관련이 없는 경우:
- 정치, 교육 정책, 경제 지표, 스포츠
- 병원 경영, 인사, 주식 정보
- 일반 건강 상식 (피부와 무관)
- 단순 광고성 기사

JSON 형식으로 응답해주세요:
{{
  "is_relevant": true/false,
  "confidence": 0.0-1.0,
  "category": "Dermatology|Aesthetics|Medical Device|Research|Not Relevant",
  "reason": "판단 근거를 한 문장으로"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a medical content classifier specializing in dermatology and aesthetic medicine."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=200
            )

            import json
            result = json.loads(response.choices[0].message.content)
            logger.debug(f"AI 판단 결과: {result}")
            return result

        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            # 에러 시 기본값 true (false negative 방지)
            return {
                "is_relevant": True,
                "confidence": 0.5,
                "category": "Error",
                "reason": f"API 오류: {str(e)}"
            }

    def is_medically_relevant(
        self,
        title: str,
        text: str,
        source: str,
        use_quick_check: bool = True
    ) -> Tuple[bool, Dict]:
        """
        기사의 의료 관련성을 판단하는 메인 함수

        Args:
            title: 기사 제목
            text: 기사 본문 또는 요약
            source: 뉴스 소스명
            use_quick_check: 키워드 사전검사 사용 여부 (기본값 True)

        Returns:
            (is_relevant, metadata) 튜플
            - is_relevant: True if 의료 관련, False otherwise
            - metadata: AI 판단 결과 딕셔너리
        """
        # 1. 키워드 사전검사
        if use_quick_check and self._quick_keyword_check(title, text):
            logger.debug(f"키워드 검사 통과: {title[:50]}...")
            return True, {
                "method": "keyword",
                "confidence": 1.0,
                "category": "Quick Pass"
            }

        # 2. 한국 뉴스 소스는 AI 검증 필수
        korean_sources = ['뷰티경제', '의학신문', '청년의사']
        is_korean_news = any(ks in source for ks in korean_sources)

        if is_korean_news or not use_quick_check:
            logger.debug(f"AI 검증 시작: {title[:50]}...")
            result = self._call_filter_api(title, text, source)

            is_relevant = result.get('is_relevant', True)
            confidence = result.get('confidence', 0.5)

            # 한국 뉴스는 confidence threshold 높게 설정
            if is_korean_news and confidence < 0.7:
                logger.info(f"필터링됨 (낮은 신뢰도): {title[:50]}... (confidence={confidence})")
                return False, result

            if not is_relevant:
                logger.info(f"필터링됨: {title[:50]}... (reason={result.get('reason')})")

            return is_relevant, result

        # 3. 기본값 (키워드 없고 AI 검증 안 함)
        logger.debug(f"기본 통과: {title[:50]}...")
        return True, {"method": "default", "confidence": 0.5}

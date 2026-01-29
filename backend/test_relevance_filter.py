"""
의료 관련성 필터 테스트 스크립트
"""

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.processor.relevance_filter import MedicalRelevanceFilter
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_filter():
    """필터 동작 테스트"""

    # 환경 변수 검증
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
        return

    filter = MedicalRelevanceFilter(api_key=settings.OPENAI_API_KEY)

    # 테스트 케이스
    test_cases = [
        {
            "title": "인천시교육청, 3월 개교 앞둔 신설학교 점검",
            "text": "인천시교육청이 신설학교 개교를 앞두고 시설 및 안전 점검을 실시했다. 교육청 관계자는 학생들의 안전한 학교생활을 위해 철저한 점검을 진행했다고 밝혔다.",
            "source": "뷰티경제",
            "expected": False,
            "description": "교육 뉴스 (관련 없음)"
        },
        {
            "title": "보톡스 신제품 출시, 주름 개선 효과 입증",
            "text": "새로운 보툴리눔 톡신 제품이 출시되었다. 임상시험 결과 기존 제품 대비 주름 개선 효과가 20% 향상된 것으로 나타났다.",
            "source": "의학신문",
            "expected": True,
            "description": "보톡스 제품 뉴스 (관련 있음)"
        },
        {
            "title": "지방의료원 정원 50% 증원... 지역별 차등 적용",
            "text": "정부가 지방의료원 의료진 정원을 50% 증원하기로 했다. 지역별 인력 수요를 고려해 차등 적용할 예정이다.",
            "source": "청년의사",
            "expected": False,
            "description": "병원 정책 뉴스 (관련 없음)"
        },
        {
            "title": "엑소좀 화장품 시장 급성장, 피부재생 효과 주목",
            "text": "엑소좀을 활용한 화장품 시장이 급성장하고 있다. 피부재생 및 안티에이징 효과가 입증되면서 소비자들의 관심이 높아지고 있다.",
            "source": "뷰티경제",
            "expected": True,
            "description": "엑소좀 화장품 뉴스 (관련 있음)"
        },
        {
            "title": "Botulinum toxin for facial wrinkles: A randomized controlled trial",
            "text": "This study evaluates the efficacy and safety of botulinum toxin type A for the treatment of facial wrinkles. Results show significant improvement in wrinkle severity scores.",
            "source": "Dermatology Times",
            "expected": True,
            "description": "보톡스 논문 (관련 있음)"
        },
        {
            "title": "코스닥 바이오 주가 급등, 신약 개발 기대감",
            "text": "코스닥 바이오 섹터가 신약 개발 기대감에 강세를 보이고 있다. 주요 바이오 기업들의 임상시험 진행 소식이 투자자들의 관심을 끌고 있다.",
            "source": "의학신문",
            "expected": False,
            "description": "주식 뉴스 (관련 없음)"
        }
    ]

    print("\n" + "="*80)
    print("의료 관련성 필터 테스트 시작")
    print("="*80 + "\n")

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n[테스트 케이스 {i}] {test['description']}")
        print(f"제목: {test['title'][:60]}...")
        print(f"소스: {test['source']}")
        print(f"예상 결과: {'관련 있음' if test['expected'] else '관련 없음'}")

        # AI 검증 강제 실행 (키워드 사전검사 비활성화)
        is_relevant, meta = filter.is_medically_relevant(
            test['title'], test['text'], test['source'], use_quick_check=False
        )

        print(f"실제 결과: {'관련 있음' if is_relevant else '관련 없음'}")
        print(f"메타데이터: {meta}")

        if is_relevant == test['expected']:
            print("✓ 통과")
            passed += 1
        else:
            print("✗ 실패")
            failed += 1

    print("\n" + "="*80)
    print(f"테스트 완료: {passed}개 통과, {failed}개 실패")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_filter()

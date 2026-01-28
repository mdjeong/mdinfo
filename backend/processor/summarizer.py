import openai
from openai import RateLimitError, APIError, APIConnectionError
import json
import logging
import sys
import os
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from article_types import SummaryResult

logger = logging.getLogger(__name__)


class Summarizer:
    def __init__(self, api_key: str = None):
        api_key = api_key or settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.text_limit = settings.OPENAI_TEXT_LIMIT

        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY가 설정되지 않았습니다. "
                ".env 파일을 확인하거나 환경 변수를 설정해주세요."
            )
        self.client = openai.OpenAI(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((RateLimitError, APIError, APIConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _call_api(self, prompt: str) -> SummaryResult:
        """OpenAI API 호출 (재시도 포함)"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond strictly in JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content.strip())

    def summarize(self, title: str, text: str, context: str = "dermatology research") -> SummaryResult:
        prompt = f"""
        당신은 피부과 전문의 및 연구원을 위한 전문 요약 조수입니다.
        다음 논문/기사의 제목과 본문을 읽고 한국어로 번역 및 요약해주세요.

        [Context]: {context}
        [Title]: {title}
        [Text]:
        {text[:self.text_limit]}

        [요청사항]:
        1. "title_ko": 제목을 학술적인 한국어로 자연스럽게 번역할 것.
        2. "summary": 핵심 연구 목적, 방법, 주요 결과, 임상적 의의를 포함하여 300자 내외 한국어로 요약할 것.
        3. 반환 형식은 반드시 JSON 포맷이어야 함: {{"title_ko": "...", "summary": "..."}}
        """

        try:
            return self._call_api(prompt)
        except Exception as e:
            logger.error(f"요약 실패: {type(e).__name__}")
            return {"title_ko": None, "summary": "Summarization failed due to an error."}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    summarizer = Summarizer()
    sample_text = """
    Botulinum toxin type A (BoNT-A) is widely used for facial rejuvenation.
    This study aims to evaluate the long-term efficacy and safety of a new BoNT-A formulation...
    """
    print(summarizer.summarize("BoNT-A Study", sample_text))

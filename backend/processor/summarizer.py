import openai
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Summarizer:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        if not api_key:
            logger.warning("OPENAI_API_KEY 미설정. 요약 기능 비활성화.")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=api_key)

    def summarize(self, title: str, text: str, context: str = "dermatology research") -> dict:
        if not self.client:
            return {"title_ko": None, "summary": "Summarization unavailable: API key missing."}

        prompt = f"""
        당신은 피부과 전문의 및 연구원을 위한 전문 요약 조수입니다.
        다음 논문/기사의 제목과 본문을 읽고 한국어로 번역 및 요약해주세요.

        [Context]: {context}
        [Title]: {title}
        [Text]:
        {text[:4000]}

        [요청사항]:
        1. "title_ko": 제목을 학술적인 한국어로 자연스럽게 번역할 것.
        2. "summary": 핵심 연구 목적, 방법, 주요 결과, 임상적 의의를 포함하여 300자 내외 한국어로 요약할 것.
        3. 반환 형식은 반드시 JSON 포맷이어야 함: {{"title_ko": "...", "summary": "..."}}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Respond strictly in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            logger.error(f"요약 실패: {e}", exc_info=True)
            return {"title_ko": None, "summary": "Summarization failed due to an error."}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    summarizer = Summarizer()
    sample_text = """
    Botulinum toxin type A (BoNT-A) is widely used for facial rejuvenation.
    This study aims to evaluate the long-term efficacy and safety of a new BoNT-A formulation...
    """
    print(summarizer.summarize("BoNT-A Study", sample_text))

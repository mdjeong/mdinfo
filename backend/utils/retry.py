"""재시도 로직 유틸리티"""

import logging
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# HTTP 요청용 재시도 설정
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=2, max=10),
    "retry": retry_if_exception_type(
        (
            requests.RequestException,
            requests.Timeout,
            ConnectionError,
        )
    ),
    "before_sleep": before_sleep_log(logger, logging.WARNING),
}

# OpenAI API용 재시도 설정 (더 긴 대기 시간)
OPENAI_RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=2, min=4, max=30),
    "before_sleep": before_sleep_log(logger, logging.WARNING),
}


@retry(**RETRY_CONFIG)
def fetch_with_retry(
    url: str,
    timeout: int = 10,
    headers: dict = None,
    **kwargs,
) -> requests.Response:
    """재시도 기능이 포함된 HTTP GET 요청

    Args:
        url: 요청할 URL
        timeout: 타임아웃 (초)
        headers: HTTP 헤더
        **kwargs: requests.get에 전달할 추가 인자

    Returns:
        requests.Response 객체
    """
    default_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    if headers:
        default_headers.update(headers)

    response = requests.get(url, headers=default_headers, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response

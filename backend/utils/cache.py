"""간단한 TTL 캐시 유틸리티"""

import time
import hashlib
import logging
from functools import wraps
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """TTL(Time-To-Live) 기반 인메모리 캐시"""

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: 기본 캐시 유효 시간 (초), 기본값 5분
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl

    def _make_key(self, *args, **kwargs) -> str:
        """인자들로부터 캐시 키 생성"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """캐시에 값 저장"""
        ttl = ttl or self._default_ttl
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    def delete(self, key: str) -> None:
        """캐시에서 값 삭제"""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """전체 캐시 초기화"""
        self._cache.clear()

    def cleanup(self) -> int:
        """만료된 항목 정리, 삭제된 항목 수 반환"""
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items() if now > v["expires_at"]
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# 전역 캐시 인스턴스
_cache = TTLCache(default_ttl=300)


def cached(ttl: int = 300, key_prefix: str = ""):
    """함수 결과를 캐싱하는 데코레이터

    Args:
        ttl: 캐시 유효 시간 (초)
        key_prefix: 캐시 키 접두사

    Example:
        @cached(ttl=60, key_prefix="articles")
        def get_articles(skip: int, limit: int):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            key = f"{key_prefix}:{func.__name__}:{_cache._make_key(*args, **kwargs)}"

            # 캐시 조회
            result = _cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit: {key}")
                return result

            # 함수 실행 및 캐시 저장
            logger.debug(f"Cache miss: {key}")
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator


def invalidate_cache(key_prefix: str = "") -> None:
    """특정 접두사를 가진 캐시 항목 무효화"""
    if not key_prefix:
        _cache.clear()
        return

    keys_to_delete = [k for k in _cache._cache.keys() if k.startswith(key_prefix)]
    for key in keys_to_delete:
        _cache.delete(key)


def get_cache() -> TTLCache:
    """전역 캐시 인스턴스 반환"""
    return _cache

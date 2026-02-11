import json
import hashlib
import logging
from typing import Any, Optional
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD or None,
    db=settings.REDIS_DB,
    decode_responses=True,
    max_connections=20
)

def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_redis_pool)


DEFAULT_TTL = 3600  # 1小时

def cache_get(key: str) -> Optional[Any]:
    try:
        raw = get_redis().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis cache_get 失败 {key}: {e}")
        return None

def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    try:
        get_redis().set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
    except Exception as e:
        logger.warning(f"Redis cache_set 失败 {key}: {e}")


def make_hash_key(prefix: str, **kwargs) -> str:
    raw = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"{prefix}:{h}"

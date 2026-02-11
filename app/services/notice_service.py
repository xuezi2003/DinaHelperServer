from sqlalchemy.orm import Session
from app.models.models import Notice
from app.db.redis import cache_get, cache_set
from app.core.config import settings

NOTICE_TTL = 300  # 5分钟，短 TTL 保证直接改 DB 也能很快生效

# 数据库无记录时的默认值（来自 env 配置）
DEFAULTS = {
    "index": settings.NOTICE_INDEX,
    "rec": settings.NOTICE_REC,
    "gpa": settings.NOTICE_GPA,
    "fail": settings.NOTICE_FAIL,
}


def _cache_key(key: str) -> str:
    return f"notice:{key}"


class NoticeService:
    @staticmethod
    def get(db: Session, key: str) -> str:
        cached = cache_get(_cache_key(key))
        if cached is not None:
            return cached

        row = db.query(Notice).filter(Notice.key == key).first()
        content = row.content if row else DEFAULTS.get(key, "")
        cache_set(_cache_key(key), content, NOTICE_TTL)
        return content


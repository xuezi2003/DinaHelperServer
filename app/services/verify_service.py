import json
import uuid
import random
import logging
from typing import List
from sqlalchemy.orm import Session
from app.services.repositories import CourseScoreRepository
from app.db.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)

CHALLENGE_TTL = 300  # 5分钟
SESSION_TTL = 86400  # 24小时
FAIL_LIMIT = 5
FAIL_BASE_COOLDOWN = 300  # 5分钟基础冷却
FAIL_COUNT_TTL = 86400  # 24小时（自动清理，非窗口）
CHALLENGE_RATE_LIMIT = settings.CHALLENGE_RATE_LIMIT
CHALLENGE_RATE_WINDOW = 300  # 5分钟
BAN_COUNT_TTL = 172800  # 48小时


class VerifyService:
    @staticmethod
    def _rate_id(openid: str, client_ip: str) -> str:
        return openid or client_ip

    @staticmethod
    def create_challenge(db: Session, sid: str, client_ip: str = "", openid: str = "") -> dict:
        r = get_redis()
        rid = VerifyService._rate_id(openid, client_ip)

        if rid:
            ban_key = f"ban_active:{rid}"
            ban_ttl = r.ttl(ban_key)
            if ban_ttl and ban_ttl > 0:
                logger.warning(f"频率限制(封禁): rid={rid} sid={sid} ttl={ban_ttl}")
                return {"cooldown": True, "ttl": ban_ttl}

            rate_key = f"challenge_rate:{rid}"
            rate = r.incr(rate_key)
            if rate == 1:
                r.expire(rate_key, CHALLENGE_RATE_WINDOW)
            if rate > CHALLENGE_RATE_LIMIT:
                logger.warning(f"频率限制(频繁): rid={rid} sid={sid} rate={rate}")
                return {"cooldown": True, "ttl": CHALLENGE_RATE_WINDOW}

        courses = CourseScoreRepository.get_by_student_id(db, sid)
        token = str(uuid.uuid4())

        # 只从最新学期的课程中出题
        if courses:
            latest_term = max(c.cTerm for c in courses)
            latest_courses = [c for c in courses if c.cTerm == latest_term and c.score is not None]
        else:
            latest_courses = []

        if len(latest_courses) < 1:
            r.set(f"challenge:{token}", json.dumps({
                "sid": sid,
                "rid": rid,
                "questions": [],
                "verified": True
            }), ex=CHALLENGE_TTL)
            return {"token": token, "questions": []}

        selected = random.sample(latest_courses, 1)
        r.set(f"challenge:{token}", json.dumps({
            "sid": sid,
            "rid": rid,
            "questions": [{"courseName": c.courseName, "score": c.score} for c in selected],
            "verified": False
        }), ex=CHALLENGE_TTL)

        return {
            "token": token,
            "questions": [c.courseName for c in selected]
        }

    @staticmethod
    def _incr_fail(r, rid: str):
        key = f"verify_fail:{rid}"
        count = r.incr(key)
        r.expire(key, FAIL_COUNT_TTL)
        if int(count) >= FAIL_LIMIT:
            ban_count_key = f"ban_count:{rid}"
            ban_count = r.incr(ban_count_key)
            cooldown = FAIL_BASE_COOLDOWN * (2 ** (int(ban_count) - 1))
            r.expire(ban_count_key, max(BAN_COUNT_TTL, cooldown))
            r.set(f"ban_active:{rid}", 1, ex=cooldown)
            r.delete(key)
            logger.warning(f"封禁升级: rid={rid} ban_count={ban_count} cooldown={cooldown}s")

    @staticmethod
    def verify_and_consume(token: str, sid: str, answers: List[dict], client_ip: str = "", openid: str = ""):
        r = get_redis()
        raw = r.get(f"challenge:{token}")
        if not raw:
            logger.info(f"验证失败: token 不存在, sid={sid}")
            return False

        challenge = json.loads(raw)
        rid = challenge.get("rid") or VerifyService._rate_id(openid, client_ip)

        if rid:
            if r.exists(f"ban_active:{rid}"):
                r.delete(f"challenge:{token}")
                logger.warning(f"验证拒绝(已封禁): rid={rid} sid={sid}")
                return False

        if challenge["sid"] != sid:
            r.delete(f"challenge:{token}")
            logger.warning(f"验证失败: sid 不匹配, 期望={challenge['sid']} 实际={sid} rid={rid}")
            return False

        if challenge["verified"]:
            r.delete(f"challenge:{token}")
            session_token = str(uuid.uuid4())
            r.set(f"session:{session_token}", sid, ex=SESSION_TTL)
            logger.info(f"验证成功(自动): sid={sid} rid={rid}")
            return session_token

        for q in challenge["questions"]:
            match = next((a for a in answers if a["courseName"] == q["courseName"]), None)
            if not match:
                r.delete(f"challenge:{token}")
                if rid:
                    VerifyService._incr_fail(r, rid)
                logger.info(f"验证失败: 未答'{q['courseName']}', sid={sid} rid={rid}")
                return False
            if int(float(match["score"])) != int(q["score"]):
                r.delete(f"challenge:{token}")
                if rid:
                    VerifyService._incr_fail(r, rid)
                logger.info(f"验证失败: '{q['courseName']}'成绩错误, sid={sid} rid={rid}")
                return False

        r.delete(f"challenge:{token}")

        # 验证成功，清除失败计数和封禁记录
        if rid:
            r.delete(f"verify_fail:{rid}")
            r.delete(f"ban_count:{rid}")
        session_token = str(uuid.uuid4())
        r.set(f"session:{session_token}", sid, ex=SESSION_TTL)
        logger.info(f"验证成功: sid={sid} rid={rid}")
        return session_token

    @staticmethod
    def validate_session(session_token: str, sid: str) -> bool:
        r = get_redis()
        stored_sid = r.get(f"session:{session_token}")
        if not stored_sid:
            return False
        if stored_sid != sid:
            r.delete(f"session:{session_token}")
            return False
        return True

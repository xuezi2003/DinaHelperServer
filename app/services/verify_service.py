import json
import uuid
import random
import logging
from typing import List
from sqlalchemy.orm import Session
from app.services.repositories import CourseScoreRepository
from app.db.redis import get_redis

logger = logging.getLogger(__name__)

CHALLENGE_TTL = 300  # 5 minutes
SESSION_TTL = 86400  # 24 hours
FAIL_LIMIT = 5
FAIL_COOLDOWN = 300  # 5 minutes
CHALLENGE_RATE_LIMIT = 20  # max challenges per window
CHALLENGE_RATE_WINDOW = 300  # 5 minutes


class VerifyService:
    @staticmethod
    def create_challenge(db: Session, sid: str, client_ip: str = "") -> dict:
        r = get_redis()

        if client_ip:
            count = r.get(f"verify_fail:{client_ip}")
            if count is not None and int(count) >= FAIL_LIMIT:
                logger.warning(f"Rate limited (fail): ip={client_ip} sid={sid} fails={count}")
                return {"cooldown": True}

            rate_key = f"challenge_rate:{client_ip}"
            rate = r.incr(rate_key)
            if rate == 1:
                r.expire(rate_key, CHALLENGE_RATE_WINDOW)
            if rate > CHALLENGE_RATE_LIMIT:
                logger.warning(f"Rate limited (freq): ip={client_ip} sid={sid} rate={rate}")
                return {"cooldown": True}

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
                "questions": [],
                "verified": True
            }), ex=CHALLENGE_TTL)
            return {"token": token, "questions": []}

        selected = random.sample(latest_courses, 1)
        r.set(f"challenge:{token}", json.dumps({
            "sid": sid,
            "questions": [{"courseName": c.courseName, "score": c.score} for c in selected],
            "verified": False
        }), ex=CHALLENGE_TTL)

        return {
            "token": token,
            "questions": [c.courseName for c in selected]
        }

    @staticmethod
    def _incr_fail(r, client_ip: str):
        key = f"verify_fail:{client_ip}"
        count = r.incr(key)
        if count == 1:
            r.expire(key, FAIL_COOLDOWN)

    @staticmethod
    def verify_and_consume(token: str, sid: str, answers: List[dict], client_ip: str = ""):
        r = get_redis()
        raw = r.get(f"challenge:{token}")
        if not raw:
            logger.info(f"Verify failed: token not found, sid={sid} ip={client_ip}")
            return False

        challenge = json.loads(raw)

        if challenge["sid"] != sid:
            r.delete(f"challenge:{token}")
            logger.warning(f"Verify failed: sid mismatch, expected={challenge['sid']} got={sid} ip={client_ip}")
            return False

        if challenge["verified"]:
            r.delete(f"challenge:{token}")
            session_token = str(uuid.uuid4())
            r.set(f"session:{session_token}", sid, ex=SESSION_TTL)
            logger.info(f"Verify success (auto): sid={sid} ip={client_ip}")
            return session_token

        for q in challenge["questions"]:
            match = next((a for a in answers if a["courseName"] == q["courseName"]), None)
            if not match:
                r.delete(f"challenge:{token}")
                if client_ip:
                    VerifyService._incr_fail(r, client_ip)
                logger.info(f"Verify failed: missing answer for '{q['courseName']}', sid={sid} ip={client_ip}")
                return False
            if int(float(match["score"])) != int(q["score"]):
                r.delete(f"challenge:{token}")
                if client_ip:
                    VerifyService._incr_fail(r, client_ip)
                logger.info(f"Verify failed: wrong score for '{q['courseName']}', sid={sid} ip={client_ip}")
                return False

        r.delete(f"challenge:{token}")

        # 验证成功，生成 sessionToken
        session_token = str(uuid.uuid4())
        r.set(f"session:{session_token}", sid, ex=SESSION_TTL)
        logger.info(f"Verify success: sid={sid} ip={client_ip}")
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

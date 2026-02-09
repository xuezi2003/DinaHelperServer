import json
import uuid
import random
from typing import List
from sqlalchemy.orm import Session
from app.services.repositories import CourseScoreRepository
from app.db.redis import get_redis

CHALLENGE_TTL = 300  # 5 minutes
SESSION_TTL = 86400  # 24 hours


class VerifyService:
    @staticmethod
    def create_challenge(db: Session, sid: str) -> dict:
        courses = CourseScoreRepository.get_by_student_id(db, sid)
        token = str(uuid.uuid4())
        r = get_redis()

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
    def verify_and_consume(token: str, sid: str, answers: List[dict]):
        r = get_redis()
        raw = r.get(f"challenge:{token}")
        if not raw:
            return False

        challenge = json.loads(raw)

        if challenge["sid"] != sid:
            r.delete(f"challenge:{token}")
            return False

        if challenge["verified"]:
            r.delete(f"challenge:{token}")
            session_token = str(uuid.uuid4())
            r.set(f"session:{session_token}", sid, ex=SESSION_TTL)
            return session_token

        for q in challenge["questions"]:
            match = next((a for a in answers if a["courseName"] == q["courseName"]), None)
            if not match:
                r.delete(f"challenge:{token}")
                return False
            if int(float(match["score"])) != int(q["score"]):
                r.delete(f"challenge:{token}")
                return False

        r.delete(f"challenge:{token}")

        # 验证成功，生成 sessionToken
        session_token = str(uuid.uuid4())
        r.set(f"session:{session_token}", sid, ex=SESSION_TTL)
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

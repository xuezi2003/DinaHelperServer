import uuid
import time
import random
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.services.repositories import CourseScoreRepository

# In-memory token store: {token: {sid, questions, verified, expires_at}}
_challenge_store: Dict[str, dict] = {}

# Session token store: {sessionToken: {sid, expires_at}}
_session_store: Dict[str, dict] = {}

CHALLENGE_TTL = 300  # 5 minutes
SESSION_TTL = 86400  # 24 hours


class VerifyService:
    @staticmethod
    def create_challenge(db: Session, sid: str) -> dict:
        courses = CourseScoreRepository.get_by_student_id(db, sid)
        token = str(uuid.uuid4())

        # 只从最新学期的课程中出题
        if courses:
            latest_term = max(c.cTerm for c in courses)
            latest_courses = [c for c in courses if c.cTerm == latest_term]
        else:
            latest_courses = []

        if len(latest_courses) < 1:
            _challenge_store[token] = {
                "sid": sid,
                "questions": [],
                "verified": True,
                "expires_at": time.time() + CHALLENGE_TTL
            }
            return {"token": token, "questions": []}

        selected = random.sample(latest_courses, 1)
        _challenge_store[token] = {
            "sid": sid,
            "questions": [{"courseName": c.courseName, "score": c.score} for c in selected],
            "verified": False,
            "expires_at": time.time() + CHALLENGE_TTL
        }

        VerifyService._cleanup()

        return {
            "token": token,
            "questions": [c.courseName for c in selected]
        }

    @staticmethod
    def verify_and_consume(token: str, sid: str, answers: List[dict]):
        challenge = _challenge_store.get(token)
        if not challenge:
            return False

        if challenge["sid"] != sid:
            _challenge_store.pop(token, None)
            return False

        if time.time() > challenge["expires_at"]:
            _challenge_store.pop(token, None)
            return False

        if challenge["verified"]:
            _challenge_store.pop(token, None)
            session_token = str(uuid.uuid4())
            _session_store[session_token] = {
                "sid": sid,
                "expires_at": time.time() + SESSION_TTL
            }
            return session_token

        for q in challenge["questions"]:
            match = next((a for a in answers if a["courseName"] == q["courseName"]), None)
            if not match:
                _challenge_store.pop(token, None)
                return False
            if int(float(match["score"])) != int(q["score"]):
                _challenge_store.pop(token, None)
                return False

        _challenge_store.pop(token, None)

        # 验证成功，生成 sessionToken
        session_token = str(uuid.uuid4())
        _session_store[session_token] = {
            "sid": sid,
            "expires_at": time.time() + SESSION_TTL
        }
        return session_token

    @staticmethod
    def validate_session(session_token: str, sid: str) -> bool:
        session = _session_store.get(session_token)
        if not session:
            return False
        if session["sid"] != sid or time.time() > session["expires_at"]:
            _session_store.pop(session_token, None)
            return False
        return True

    @staticmethod
    def _cleanup():
        now = time.time()
        expired = [k for k, v in _challenge_store.items() if now > v["expires_at"]]
        for k in expired:
            del _challenge_store[k]
        expired_sessions = [k for k, v in _session_store.items() if now > v["expires_at"]]
        for k in expired_sessions:
            del _session_store[k]

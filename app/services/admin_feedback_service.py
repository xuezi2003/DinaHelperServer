from sqlalchemy.orm import Session
from app.services.repositories import FeedbackRepository


class FeedbackService:
    @staticmethod
    def add_feedback_content(db: Session, sid: str, content: str):
        FeedbackRepository.save_feedback(db, sid, content)

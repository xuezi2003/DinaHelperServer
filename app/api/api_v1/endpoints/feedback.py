from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.admin_feedback_service import FeedbackService
from app.schemas.dtos import UserFeedbackDTO
from app.schemas.result import Result

router = APIRouter()

@router.post("/content", response_model=Result[str])
def add_feedback_content(feedback: UserFeedbackDTO = Body(...), db: Session = Depends(get_db)):
    FeedbackService.add_feedback_content(db, sid=None, content=feedback.content)
    return Result.success(data="反馈成功")

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.student_service import StudentService
from app.services.verify_service import VerifyService
from app.schemas.dtos import ChallengeResponseDTO
from app.schemas.result import Result

router = APIRouter()

@router.get("/challenge", response_model=Result[ChallengeResponseDTO])
def get_challenge(sid: str = Query(..., max_length=20), db: Session = Depends(get_db)):
    student = StudentService.get_student_by_id(db, sid)
    if not student:
        return Result.error(message="查无此人")

    challenge = VerifyService.create_challenge(db, sid)
    return Result.success(data=challenge)

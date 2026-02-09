from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.student_service import StudentService
from app.services.verify_service import VerifyService
from app.schemas.dtos import ChallengeResponseDTO
from app.schemas.result import Result
from app.core.config import settings

router = APIRouter()

@router.get("/notice", response_model=Result[str])
def get_notice():
    return Result.success(data=settings.NOTICE)

@router.get("/debug-ip")
def debug_ip(request: Request):
    return {
        "CF-Connecting-IP": request.headers.get("CF-Connecting-IP"),
        "X-Forwarded-For": request.headers.get("X-Forwarded-For"),
        "X-Real-IP": request.headers.get("X-Real-IP"),
        "client.host": request.client.host
    }

@router.get("/challenge", response_model=Result[ChallengeResponseDTO])
def get_challenge(sid: str = Query(..., max_length=20), db: Session = Depends(get_db)):
    student = StudentService.get_student_by_id(db, sid)
    if not student:
        return Result.error(message="查无此人")

    challenge = VerifyService.create_challenge(db, sid)
    return Result.success(data=challenge)

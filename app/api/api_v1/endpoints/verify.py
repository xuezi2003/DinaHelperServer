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

@router.get("/challenge", response_model=Result[ChallengeResponseDTO])
def get_challenge(request: Request, sid: str = Query(..., max_length=20), db: Session = Depends(get_db)):
    client_ip = request.headers.get("CF-Connecting-IP") or request.client.host

    student = StudentService.get_student_by_id(db, sid)
    if not student:
        return Result.error(message="查无此人")

    challenge = VerifyService.create_challenge(db, sid, client_ip)
    if "cooldown" in challenge:
        return Result.error(message="验证失败次数过多，请5分钟后再试", code=429)
    return Result.success(data=challenge)

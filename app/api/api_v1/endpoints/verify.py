from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.student_service import StudentService
from app.services.verify_service import VerifyService
from app.schemas.dtos import ChallengeResponseDTO
from app.schemas.result import Result

router = APIRouter()


@router.get("/challenge", response_model=Result[ChallengeResponseDTO])
def get_challenge(request: Request, sid: str = Query(..., max_length=20), db: Session = Depends(get_db)):
    client_ip = request.headers.get("CF-Connecting-IP") or request.client.host
    openid = request.state.openid  # 由 require_wx 依赖注入

    student = StudentService.get_student_by_id(db, sid)
    if not student:
        return Result.error(message="查无此人")

    challenge = VerifyService.create_challenge(db, sid, client_ip, openid)
    if "cooldown" in challenge:
        ttl = challenge.get("ttl", 300)
        return Result.error(message=str(ttl), code=429)
    return Result.success(data=challenge)

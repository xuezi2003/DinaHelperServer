from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.student_service import StudentService
from app.services.verify_service import VerifyService
from app.services.wx_service import WxService
from app.schemas.dtos import ChallengeResponseDTO
from app.schemas.result import Result
from app.core.config import settings

router = APIRouter()

@router.get("/notice", response_model=Result[str])
def get_notice():
    return Result.success(data=settings.NOTICE)

@router.get("/challenge", response_model=Result[ChallengeResponseDTO])
def get_challenge(request: Request, sid: str = Query(..., max_length=20), wxToken: str = Query(""), db: Session = Depends(get_db)):
    client_ip = request.headers.get("CF-Connecting-IP") or request.client.host
    openid = WxService.validate_wx_token(wxToken) or ""

    if not openid:
        return Result.error(message="请通过微信小程序访问", code=401)

    student = StudentService.get_student_by_id(db, sid)
    if not student:
        return Result.error(message="查无此人")

    challenge = VerifyService.create_challenge(db, sid, client_ip, openid)
    if "cooldown" in challenge:
        ttl = challenge.get("ttl", 300)
        return Result.error(message=str(ttl), code=429)
    return Result.success(data=challenge)

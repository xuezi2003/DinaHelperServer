from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.student_service import StudentService
from app.services.verify_service import VerifyService
from app.services.wx_service import WxService
from app.schemas.dtos import RankDTO, SameNameDTO, VerifiedQueryDTO
from app.schemas.result import Result

router = APIRouter()

@router.post("/rank/id")
def get_rank_by_id(body: VerifiedQueryDTO, request: Request, db: Session = Depends(get_db)):
    session_token = None
    client_ip = request.headers.get("CF-Connecting-IP") or request.client.host
    openid = (WxService.validate_wx_token(body.wxToken) or "") if body.wxToken else ""

    if body.sessionToken:
        if not VerifyService.validate_session(body.sessionToken, body.sid):
            return Result.error(message="会话已过期，请重新验证", code=403)
        session_token = body.sessionToken
    else:
        result = VerifyService.verify_and_consume(body.token, body.sid, [a.model_dump() for a in body.answers], client_ip, openid)
        if not result:
            return Result.error(message="验证失败，请确认成绩是否正确", code=403)
        session_token = result

    student = StudentService.get_student_by_id(db, body.sid)
    if not student:
        return Result.error(message="查无此人")
    
    rank_dto = StudentService.get_student_rank(db, body.sid)
    return Result.success(data={"sessionToken": session_token, "rankData": rank_dto.model_dump()})

@router.get("/query/py", response_model=Result[List[SameNameDTO]])
def get_students_by_pinyin(spy: str = Query(..., max_length=20), db: Session = Depends(get_db)):
    students = StudentService.get_students_by_pinyin(db, spy)
    return Result.success(data=students)

@router.get("/query/name", response_model=Result[List[SameNameDTO]])
def get_students_by_name(sname: str = Query(..., max_length=20), db: Session = Depends(get_db)):
    students = StudentService.get_students_by_name(db, sname)
    return Result.success(data=students)

@router.get("/rank/major")
def get_major_ranking(
    sid: str = Query(..., max_length=20, description="学号，用于获取专业信息"),
    sortBy: str = Query("gpa", pattern="^(gpa|avg)$", description="排序字段: gpa 或 avg"),
    order: str = Query("desc", pattern="^(desc|asc)$", description="排序方式: desc 或 asc"),
    db: Session = Depends(get_db)
):
    student = StudentService.get_student_by_id(db, sid)
    if not student:
        return Result.error(message="查无此人")
    
    ranking = StudentService.get_major_ranking_list(db, student, sortBy, order)
    return Result.success(data=ranking)

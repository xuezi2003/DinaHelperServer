from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.student_service import StudentService
from app.services.course_score_service import CourseScoreService
from app.schemas.schemas import ScoreQueryDTO, CourseScoreBase
from app.schemas.dtos import CourseInfoFilterDTO, FailRateStatisDTO, VerifiedQueryDTO
from app.schemas.result import Result
from app.api.deps import verify_request


router = APIRouter()


@router.post("/query/id")
def get_score_by_id(body: VerifiedQueryDTO, request: Request, db: Session = Depends(get_db)):
    session_token = verify_request(body, request)

    student = StudentService.get_student_by_id(db, body.sid)
    if not student:
        return Result.error(message="查无此人")
    
    course_scores = CourseScoreService.get_scores_by_student_id(db, student.studentId)
    scores_data = [CourseScoreBase.model_validate(cs) for cs in course_scores]
    
    query_dto = ScoreQueryDTO(
        avg=student.sAvg,
        gpa=student.sGpa,
        dataList=scores_data
    )
    return Result.success(data={"sessionToken": session_token, "queryData": query_dto.model_dump()})

@router.get("/name", response_model=Result[List[str]])
def get_course_name(cname: str = Query(..., alias="cname", max_length=50), db: Session = Depends(get_db)):
    names = CourseScoreService.get_course_names(db, cname)
    if not names:
        return Result.error(message="没有匹配课程")
    return Result.success(data=names)

@router.get("/filter", response_model=Result[CourseInfoFilterDTO])
def get_course_info_filter_by_name(courseName: str = Query(..., max_length=50), db: Session = Depends(get_db)):
    current_filter = CourseInfoFilterDTO(courseName=courseName)
    options = CourseScoreService.get_dynamic_filter_options(db, current_filter)
    if not options.terms:
        return Result.error(message="没有匹配课程")
    return Result.success(data=options)

@router.post("/filter/dynamic", response_model=Result[CourseInfoFilterDTO])
def get_dynamic_filter_options(currentFilter: CourseInfoFilterDTO = Body(...), db: Session = Depends(get_db)):
    options = CourseScoreService.get_dynamic_filter_options(db, currentFilter)
    return Result.success(data=options)

@router.post("/fail-rate", response_model=Result[FailRateStatisDTO])
def get_fail_rate_statis(filter: CourseInfoFilterDTO = Body(...), db: Session = Depends(get_db)):
    stats = CourseScoreService.get_fail_rate_statistics(db, filter)
    return Result.success(data=stats)

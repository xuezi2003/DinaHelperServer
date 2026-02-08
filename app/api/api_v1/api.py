from fastapi import APIRouter

from app.api.api_v1.endpoints import course, student, feedback

api_router = APIRouter()

api_router.include_router(course.router, prefix="/cs", tags=["course_score"])
api_router.include_router(student.router, prefix="/stu", tags=["student"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])

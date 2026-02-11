from fastapi import APIRouter, Depends

from app.api.api_v1.endpoints import auth, course, student, verify, recommendation, notice
from app.api.deps import require_wx

api_router = APIRouter()

# 无需鉴权
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(notice.router, prefix="/notice", tags=["notice"])

# 需要微信鉴权（通过 X-Wx-Token 请求头）
_wx = [Depends(require_wx)]
api_router.include_router(course.router, prefix="/cs", tags=["course_score"], dependencies=_wx)
api_router.include_router(student.router, prefix="/stu", tags=["student"], dependencies=_wx)
api_router.include_router(verify.router, prefix="/verify", tags=["verify"], dependencies=_wx)
api_router.include_router(recommendation.router, prefix="/rec", tags=["recommendation"], dependencies=_wx)

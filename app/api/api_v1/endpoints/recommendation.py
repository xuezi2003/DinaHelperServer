from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.result import Result
from app.schemas.dtos import RecFilterDTO, RecOptionsDTO, RecListResponseDTO
from app.services.recommendation_service import RecommendationService
from typing import Optional

router = APIRouter()


@router.get("/options", response_model=Result[RecOptionsDTO])
def get_options(
    year: Optional[int] = None,
    college: Optional[str] = None,
    db: Session = Depends(get_db),
):
    options = RecommendationService.get_options(db, year, college)
    return Result.success(data=options)


@router.post("/list", response_model=Result[RecListResponseDTO])
def get_rec_list(
    f: RecFilterDTO,
    db: Session = Depends(get_db),
):
    if not f.year:
        return Result.error(message="请选择年份", code=400)
    f.page = max(1, f.page)
    f.pageSize = max(1, f.pageSize)
    data = RecommendationService.query_list(db, f)
    return Result.success(data=data)

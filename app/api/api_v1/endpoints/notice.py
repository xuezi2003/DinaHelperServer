from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.result import Result
from app.services.notice_service import NoticeService

router = APIRouter()


@router.get("/{key}")
def get_notice(key: str = Path(..., max_length=20), db: Session = Depends(get_db)):
    content = NoticeService.get(db, key)
    return Result.success(data=content)

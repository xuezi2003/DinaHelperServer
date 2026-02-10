from fastapi import APIRouter, Body
from app.services.wx_service import WxService
from app.schemas.result import Result

router = APIRouter()

@router.post("/wxlogin")
def wx_login(code: str = Body(..., embed=True)):
    result = WxService.login(code)
    if "error" in result:
        return Result.error(message=result["error"])
    return Result.success(data=result)

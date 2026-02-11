from fastapi import Request, Header, HTTPException
from app.services.wx_service import WxService
from app.services.verify_service import VerifyService
from app.schemas.dtos import VerifiedQueryDTO


def require_wx(request: Request, x_wx_token: str = Header("")):
    """路由级依赖：从 X-Wx-Token 请求头校验微信身份，通过后将 openid 存入 request.state。"""
    openid = WxService.validate_wx_token(x_wx_token) if x_wx_token else None
    if not openid:
        raise HTTPException(status_code=401, detail="请通过微信小程序访问")
    request.state.openid = openid


def verify_request(body: VerifiedQueryDTO, request: Request) -> str:
    """统一的身份验证逻辑。成功返回 session_token，失败直接抛 HTTPException。"""
    client_ip = request.headers.get("CF-Connecting-IP") or request.client.host
    openid = getattr(request.state, "openid", "")

    if body.sessionToken:
        if not VerifyService.validate_session(body.sessionToken, body.sid):
            raise HTTPException(status_code=403, detail="会话已过期，请重新验证")
        return body.sessionToken

    result = VerifyService.verify_and_consume(
        body.token, body.sid,
        [a.model_dump() for a in body.answers],
        client_ip, openid,
    )
    if not result:
        raise HTTPException(status_code=403, detail="验证失败，请确认成绩是否正确")
    return result

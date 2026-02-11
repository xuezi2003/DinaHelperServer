import uuid
import logging
import httpx
from app.db.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)

WX_SESSION_TTL = 7200  # 2小时

class WxService:
    @staticmethod
    def login(code: str) -> dict:
        """用 wx.login code 换取 openid，返回 wxToken。"""
        r = get_redis()

        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.WX_APP_ID,
            "secret": settings.WX_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        try:
            resp = httpx.get(url, params=params, timeout=5)
            data = resp.json()
        except Exception as e:
            logger.error(f"微信 API 请求失败: {e}")
            return {"error": "微信服务异常，请稍后重试"}

        if "errcode" in data and data["errcode"] != 0:
            logger.warning(f"微信登录失败: errcode={data.get('errcode')} errmsg={data.get('errmsg')}")
            return {"error": "微信登录失败"}

        openid = data.get("openid")
        if not openid:
            logger.warning(f"微信登录: 响应中无 openid")
            return {"error": "微信登录失败"}

        wx_token = str(uuid.uuid4())
        r.set(f"wx_session:{wx_token}", openid, ex=WX_SESSION_TTL)
        logger.info(f"微信登录成功: openid={openid[:8]}***")
        return {"wxToken": wx_token}

    @staticmethod
    def validate_wx_token(wx_token: str) -> str | None:
        """验证 wxToken，返回 openid，无效则返回 None。"""
        if not wx_token:
            return None
        r = get_redis()
        openid = r.get(f"wx_session:{wx_token}")
        return openid

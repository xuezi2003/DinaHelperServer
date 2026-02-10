from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "DinaHelper"
    API_V1_STR: str = "/kldj"
    PORT: int = 3099
    NOTICE: str = "数据仅供参考，请以教务系统为准。查询前需回答一门课程成绩以验证身份，通过后24小时内免验证"
    
    # Database
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # Rate Limiting
    CHALLENGE_RATE_LIMIT: int = 10

    # WeChat
    WX_APP_ID: str = ""
    WX_APP_SECRET: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()

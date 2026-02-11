from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "DinaHelper"
    API_V1_STR: str = "/kldj"
    PORT: int = 3099
    
    # 数据库
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    # Redis 缓存
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # 频率限制
    CHALLENGE_RATE_LIMIT: int = 10

    # 公告默认值（数据库无记录时的回退）
    NOTICE_INDEX: str = "数据仅供参考，请以教务系统为准。查询前需回答一门课程成绩以验证身份，通过后24小时内免验证"
    NOTICE_REC: str = "数据来源：历年推免公示名单+成绩库。「推免时」为公示时数据，「最新」为成绩库最新数据。2024年无表现成绩和专业人数。本页不展示任何个人身份信息。"
    NOTICE_GPA: str = "因重修/补考/刷分/公选等情况，计算结果可能存在偏差，请以教务系统为准"
    NOTICE_FAIL: str = "快速了解课程难度"

    # 微信
    WX_APP_ID: str = ""
    WX_APP_SECRET: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()

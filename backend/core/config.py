from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ChineseLearn"
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:19006"

    # Database
    DATABASE_URL: str = "postgresql://chineselearn:chineselearn123@postgres:5432/chineselearn"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Auth / JWT
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

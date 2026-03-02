from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str
    google_news_api_key: Optional[str] = None  # 可选，不配置时使用备用搜索
    brave_api_key: Optional[str] = None  # 可选备用搜索 API
    cors_origins: str = "http://localhost:3000"
    debug: bool = True

    # AI Agent Configuration
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    llm_model_name: str = "moonshotai/kimi-k2.5"

    class Config:
        env_file = ".env"


settings = Settings()

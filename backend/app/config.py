"""集中管理配置。所有值都能被 .env 或环境变量覆盖。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./tracker.db"
    anthropic_api_key: str = ""
    api_key: str = ""                 # 留空 = 不校验(本地开发)
    daily_review_cap: int = 4         # 每天最多复习几道
    daily_new_cap: int = 3            # 每天最多做几道新题
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

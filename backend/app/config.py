"""Central configuration. Every value can be overridden via .env or environment vars."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./tracker.db"

    # LLM provider: "none" | "anthropic" | "deepseek"
    llm_provider: str = "none"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-flash"
    deepseek_base_url: str = "https://api.deepseek.com"

    # Which timezone defines "today". Empty means the machine's local zone, which is what
    # you want for a personal tracker: practising at 9pm should count towards that evening,
    # not towards tomorrow. Set e.g. TIMEZONE=America/Toronto to pin it.
    timezone: str = ""

    api_key: str = ""                 # empty = no auth (local dev)
    daily_review_cap: int = 4         # max reviews per day
    daily_new_cap: int = 3            # max new problems per day
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

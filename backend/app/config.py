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
    # Interleaving: at most this many reviews per chapter / per primary pattern each day.
    # 0 disables the limit. Unused slots are always backfilled, so a limit never shrinks
    # the day — it only changes which problems fill it.
    daily_per_chapter_cap: int = 2
    daily_per_pattern_cap: int = 2
    # New problems: one per chapter a day, so a fresh day samples several topics instead of
    # three in a row from the same chapter. Backfilled like reviews.
    daily_new_per_chapter_cap: int = 1
    # Hold every Hard back until the Easy/Medium problems are done — the same rule as the
    # manual study plan. Set to false when you are ready to start on Hards.
    new_hard_last: bool = True
    # Finish the NeetCode 150 before any of the 250 additions, which then come in a fixed
    # shuffled order rather than chapter by chapter.
    new_neetcode150_first: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

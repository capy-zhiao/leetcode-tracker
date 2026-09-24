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
    # Thinking mode (DeepSeek's default is on). Reasoning tokens are billed as output.
    deepseek_thinking: bool = True
    deepseek_reasoning_effort: str = "high"     # low | high | max
    llm_timeout_seconds: int = 300              # thinking replies via a relay took up to ~160s

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
    # New problems follow the tier order strictly by default (0 = no limit). Raise these to
    # spread a day's new problems across chapters / patterns instead.
    daily_new_per_chapter_cap: int = 0
    daily_new_per_pattern_cap: int = 0
    # Hold every Hard back until the Easy/Medium problems are done — the same rule as the
    # manual study plan. Set to false when you are ready to start on Hards.
    new_hard_last: bool = True
    # Finish the NeetCode 150 before any of the 250 additions, which then come in a fixed
    # shuffled order rather than chapter by chapter.
    new_neetcode150_first: bool = True
    # Chapters whose NeetCode 150 problems wait with the 250 additions instead (CSV).
    # Default: Bit Manipulation (17) and Math & Geometry (18), which were left out of the
    # original study plan. They stay flagged as NeetCode 150 everywhere else.
    new_later_chapters: str = "17,18"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def new_later_chapter_set(self) -> frozenset[int]:
        return frozenset(int(c) for c in self.new_later_chapters.split(",") if c.strip())

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

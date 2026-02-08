from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    llm_provider: str = "claude"  # "claude" | "openai"
    llm_model: str = "claude-sonnet-4-5-20250929"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Search
    serper_api_key: str = ""  # optional, falls back to DuckDuckGo
    search_recency: str = "qdr:y2"  # Serper tbs param: qdr:y2 = past 2 years

    # Reddit
    reddit_client_id: str = ""  # optional, falls back to HTML fetch
    reddit_client_secret: str = ""

    # Infrastructure
    engine_port: int = 8000
    data_dir: Path = Path("./data")

    model_config = {
        "env_file": ("../.env", ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def db_path(self) -> Path:
        return self.data_dir / "pain_radar.db"

    @property
    def snapshots_dir(self) -> Path:
        return self.data_dir / "snapshots"

    @property
    def has_serper(self) -> bool:
        return bool(self.serper_api_key)

    @property
    def has_reddit(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()

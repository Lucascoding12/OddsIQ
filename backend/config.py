from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://oddsiq:oddsiq@localhost:5432/oddsiq"
    redis_url: str = "redis://localhost:6379"
    odds_api_key: str = ""
    odds_api_base: str = "https://api.the-odds-api.com/v4"
    # Set very high in dev to avoid burning free-tier credits
    poll_interval_seconds: int = 99999
    # Comma-separated list of allowed CORS origins. Vercel URLs are also
    # allowed via allow_origin_regex in main.py so you don't need to list them.
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]


settings = Settings()

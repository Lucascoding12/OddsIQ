from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://oddsiq:oddsiq@localhost:5432/oddsiq"
    redis_url: str = "redis://localhost:6379"
    odds_api_key: str = ""
    odds_api_base: str = "https://api.the-odds-api.com/v4"
    # Set very high in dev to avoid burning free-tier credits
    poll_interval_seconds: int = 99999


settings = Settings()

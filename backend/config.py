from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://oddsiq:oddsiq@localhost:5432/oddsiq"

    @property
    def async_database_url(self) -> str:
        """Ensure the URL uses the asyncpg driver. Railway provides postgresql://, we need postgresql+asyncpg://."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    redis_url: str = "redis://localhost:6379"
    odds_api_key: str = ""
    odds_api_base: str = "https://api.the-odds-api.com/v4"
    # Set very high in dev to avoid burning free-tier credits
    poll_interval_seconds: int = 99999
    # Comma-separated list of allowed CORS origins. Vercel URLs are also
    # allowed via allow_origin_regex in main.py so you don't need to list them.
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ── Poller ───────────────────────────────────────────────────────────────
    # Odds API cost per sport request = (#markets) × (#regions).
    # Spreads and totals are where most arbs appear, so they're on by default.
    odds_markets: str = "h2h,spreads,totals"
    # "us" covers DK/FD/MGM/Caesars/etc. Adding "us2" (ESPN Bet, Fliff, Hard Rock…)
    # or "eu"/"uk" finds more arbs but multiplies credit cost.
    odds_regions: str = "us"
    # Explicit book list; takes priority over regions. Every 10 books costs
    # the same as one region, so this stays at 20. The first four are the
    # +EV reference books in priority order (Pinnacle → Betfair → Kalshi →
    # Polymarket); the next three only cross-check; the rest are US books
    # you'd bet at. LowVig is left out because it copies BetOnline exactly.
    odds_bookmakers: str = (
        "pinnacle,betfair_ex_eu,kalshi,polymarket,betonlineag,novig,prophetx,"
        "draftkings,fanduel,betmgm,williamhill_us,fanatics,espnbet,betrivers,"
        "hardrockbet,bovada,ballybet,fliff,betparx,mybookieag"
    )
    # Explicit comma-separated sport keys. Empty → auto-discover in-season
    # sports via /sports, which is free (costs no credits).
    odds_sports: str = ""
    odds_max_sports: int = 8
    # Stop polling once remaining credits fall to this floor so the key is
    # never fully drained by the scheduler.
    odds_credit_reserve: int = 25

    # ── Arb scanner ──────────────────────────────────────────────────────────
    # Ignore book quotes whose last_update is older than this; 0 disables.
    arb_max_quote_age_seconds: int = 1800
    # In-play feeds lag the books by seconds-to-minutes; live "arbs" are
    # usually phantoms, so they're excluded unless explicitly enabled.
    arb_include_live: bool = False
    # Also keep near-misses down to this return (%) so the UI can show
    # markets that are close to flipping into an arb.
    arb_near_miss_pct: float = -1.0
    # +EV bets below this edge (%) aren't kept at all; the UI filters higher.
    ev_floor_pct: float = 0.0

    @property
    def markets_list(self) -> list[str]:
        return [m.strip() for m in self.odds_markets.split(",") if m.strip()]

    @property
    def regions_list(self) -> list[str]:
        return [r.strip() for r in self.odds_regions.split(",") if r.strip()]

    @property
    def bookmakers_list(self) -> list[str]:
        return [b.strip() for b in self.odds_bookmakers.split(",") if b.strip()]

    @property
    def sports_list(self) -> list[str]:
        return [s.strip() for s in self.odds_sports.split(",") if s.strip()]


settings = Settings()

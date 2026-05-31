"""
Odds poller — fetches live odds from The Odds API and caches them in Redis.

Architecture:
  - Called by APScheduler on an interval (POLL_INTERVAL_SECONDS).
  - Writes two key types to Redis:
      odds:sport:<sport_key>   → JSON list of games with bookmaker odds
      odds:all                 → JSON list of all sports combined (for the board)
  - Also persists OddsSnapshots to Postgres for historical tracking.

We poll a fixed set of active sports to keep credit usage low.
Adjust ACTIVE_SPORTS to expand/shrink coverage.
"""
import json
import logging
from datetime import datetime, timezone

import httpx

from config import settings
from services.redis_client import get_redis, ODDS_TTL

logger = logging.getLogger(__name__)

# Sports we actively poll. Add/remove to control credit burn.
# Each sport_key costs 1 credit per request on The Odds API.
# 4 sports × 4 polls/day × 30 days = 480 credits/month (fits free tier of 500).
# These are the sports with active schedules in 2026 May-June.
# Swap in NFL/NCAAF in September, NBA/NCAAB in October, etc.
ACTIVE_SPORTS: list[str] = [
    "baseball_mlb",        # in season
    "icehockey_nhl",       # playoffs
    "basketball_nba",      # playoffs / finals
    "soccer_usa_mls",      # in season
]

REGIONS = "us"
MARKETS = "h2h"
ODDS_FORMAT = "american"


async def fetch_odds_for_sport(client: httpx.AsyncClient, sport_key: str) -> list[dict]:
    """Fetch odds from The Odds API for one sport. Returns empty list on error."""
    try:
        resp = await client.get(
            f"{settings.odds_api_base}/sports/{sport_key}/odds",
            params={
                "apiKey": settings.odds_api_key,
                "regions": REGIONS,
                "markets": MARKETS,
                "oddsFormat": ODDS_FORMAT,
            },
            timeout=15.0,
        )
        remaining = resp.headers.get("x-requests-remaining", "?")
        used = resp.headers.get("x-requests-used", "?")
        logger.info(f"Polled {sport_key}: HTTP {resp.status_code} | credits used={used} remaining={remaining}")

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 422:
            # Sport has no active events right now
            return []
        else:
            logger.warning(f"Unexpected status {resp.status_code} for {sport_key}: {resp.text[:200]}")
            return []
    except Exception as exc:
        logger.error(f"Error fetching odds for {sport_key}: {exc}")
        return []


async def poll_all_odds() -> None:
    """
    Main polling task. Fetches all active sports and writes to Redis.
    Called by APScheduler in main.py.
    """
    if not settings.odds_api_key:
        logger.warning("ODDS_API_KEY not set — skipping poll")
        return

    redis = await get_redis()
    all_games: list[dict] = []

    async with httpx.AsyncClient() as client:
        for sport_key in ACTIVE_SPORTS:
            games = await fetch_odds_for_sport(client, sport_key)
            if games:
                # Normalize: add display fields for the frontend
                for game in games:
                    game["polled_at"] = datetime.now(timezone.utc).isoformat()

                await redis.setex(
                    f"odds:sport:{sport_key}",
                    ODDS_TTL,
                    json.dumps(games),
                )
                all_games.extend(games)

    if all_games:
        await redis.setex("odds:all", ODDS_TTL, json.dumps(all_games))
        logger.info(f"Poll complete: {len(all_games)} games cached across {len(ACTIVE_SPORTS)} sports")
    else:
        logger.info("Poll complete: no active games found")

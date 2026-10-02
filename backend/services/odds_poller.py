"""
Odds poller — fetches live odds from The Odds API into the in-memory store.

Each poll:
  1. Picks sports: ODDS_SPORTS if set, otherwise auto-discovers in-season
     sports via /sports (free — costs no credits), cached for an hour.
  2. Fetches every sport concurrently over one keep-alive HTTP client.
  3. Hands the merged snapshot to the store, which rescans for arbs at once.
  4. Writes the snapshot to Redis (best effort) for warm restarts.

Credits: each sport request costs (#markets × #regions). The remaining
balance comes back in response headers; once it would dip below
ODDS_CREDIT_RESERVE the poller stops spending instead of draining the key.
"""
import asyncio
import logging
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import orjson

from config import settings
from services.odds_store import store
from services.redis_client import ODDS_TTL, get_redis

logger = logging.getLogger(__name__)

# When auto-discovering, these go first; anything else in-season fills the
# remaining ODDS_MAX_SPORTS slots in the order the API lists it.
SPORT_PRIORITY: list[str] = [
    "americanfootball_nfl",
    "basketball_nba",
    "baseball_mlb",
    "icehockey_nhl",
    "americanfootball_ncaaf",
    "basketball_ncaab",
    "basketball_wnba",
    "mma_mixed_martial_arts",
    "soccer_epl",
    "soccer_usa_mls",
    "soccer_uefa_champs_league",
    "boxing_boxing",
]
DISCOVERY_GROUPS = {
    "American Football", "Basketball", "Baseball", "Ice Hockey",
    "Soccer", "Mixed Martial Arts", "Boxing", "Tennis",
}
DISCOVERY_TTL_SECONDS = 3600
# Local fallback when Redis isn't available (e.g. dev), so restarts don't re-spend credits.
SNAPSHOT_FILE = Path(__file__).resolve().parent.parent / ".cache" / "odds_snapshot.json"

_client: httpx.AsyncClient | None = None
_poll_lock = asyncio.Lock()
_discovered: list[str] = []
_discovered_at = 0.0
# sport → last successful payload, so one failed request doesn't blank a sport
_last_good: dict[str, list[dict]] = {}


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.odds_api_base,
            timeout=httpx.Timeout(15.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=10),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _record_credits(resp: httpx.Response) -> None:
    remaining = resp.headers.get("x-requests-remaining")
    used = resp.headers.get("x-requests-used")
    last = resp.headers.get("x-requests-last")
    if remaining is not None:
        store.stats.credits_remaining = int(float(remaining))
    if used is not None:
        store.stats.credits_used = int(float(used))
    if last is not None:
        store.stats.last_call_cost = int(float(last))


def rank_sports(available: list[dict], max_sports: int) -> list[str]:
    """Choose which in-season sports to poll, majors first."""
    candidates = [
        s["key"] for s in available
        if s.get("active") and not s.get("has_outrights") and s.get("group") in DISCOVERY_GROUPS
    ]
    priority = {key: i for i, key in enumerate(SPORT_PRIORITY)}
    candidates.sort(key=lambda k: priority.get(k, len(priority)))
    return candidates[:max_sports]


async def select_sports() -> list[str]:
    global _discovered, _discovered_at
    if settings.sports_list:
        return settings.sports_list
    if _discovered and time.monotonic() - _discovered_at < DISCOVERY_TTL_SECONDS:
        return _discovered
    try:
        resp = await _get_client().get("/sports", params={"apiKey": settings.odds_api_key})
        resp.raise_for_status()
        _discovered = rank_sports(orjson.loads(resp.content), settings.odds_max_sports)
        _discovered_at = time.monotonic()
        logger.info(f"Discovered in-season sports: {_discovered}")
    except Exception as exc:
        logger.warning(f"Sport discovery failed, keeping previous list: {exc}")
    return _discovered or SPORT_PRIORITY[:4]


async def fetch_sport(sport_key: str) -> list[dict] | None:
    """Odds for one sport. [] when it has no events; None on failure."""
    try:
        params = {
            "apiKey": settings.odds_api_key,
            "markets": ",".join(settings.markets_list),
            "oddsFormat": "american",
            "dateFormat": "iso",
        }
        if settings.bookmakers_list:
            params["bookmakers"] = ",".join(settings.bookmakers_list)
        else:
            params["regions"] = ",".join(settings.regions_list)
        resp = await _get_client().get(f"/sports/{sport_key}/odds", params=params)
    except httpx.HTTPError as exc:
        logger.error(f"Fetch {sport_key} failed: {exc}")
        store.stats.last_error = f"{sport_key}: {exc}"
        return None

    _record_credits(resp)
    if resp.status_code == 200:
        return orjson.loads(resp.content)
    if resp.status_code in (404, 422):
        return []  # sport off-season or no events
    logger.warning(f"{sport_key}: HTTP {resp.status_code} {resp.text[:200]}")
    store.stats.last_error = f"{sport_key}: HTTP {resp.status_code}"
    return None


def _estimated_cost(n_sports: int) -> int:
    books = settings.bookmakers_list
    regions = math.ceil(len(books) / 10) if books else len(settings.regions_list)
    return n_sports * len(settings.markets_list) * regions


async def poll_all_odds() -> None:
    """Fetch, merge, publish. Overlapping calls (scheduler + manual) are serialized."""
    if not settings.odds_api_key:
        logger.warning("ODDS_API_KEY not set — skipping poll")
        return

    async with _poll_lock:
        sports = await select_sports()
        remaining = store.stats.credits_remaining
        cost = _estimated_cost(len(sports))
        if remaining is not None and remaining - cost < settings.odds_credit_reserve:
            store.stats.last_error = (
                f"Credit reserve reached ({remaining} left, poll costs ~{cost}); polling paused"
            )
            logger.warning(store.stats.last_error)
            return

        start = time.perf_counter()
        results = await asyncio.gather(*(fetch_sport(s) for s in sports))
        store.stats.fetch_ms = (time.perf_counter() - start) * 1000

        polled_at = datetime.now(timezone.utc).isoformat()
        all_games: list[dict] = []
        for sport, games in zip(sports, results):
            if games is None:
                games = _last_good.get(sport, [])
            else:
                for g in games:
                    g["polled_at"] = polled_at
                _last_good[sport] = games
            all_games.extend(games)
        for stale in set(_last_good) - set(sports):
            del _last_good[stale]

        if all(r is not None for r in results):
            store.stats.last_error = None
        store.stats.sports = sports
        store.update(all_games, polled_at)

    await _persist(all_games, polled_at)


async def _persist(games: list[dict], polled_at: str) -> None:
    """Best-effort copies for warm restarts; the API never reads them per request."""
    payload = orjson.dumps(games)
    try:
        SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_FILE.write_bytes(orjson.dumps({"polled_at": polled_at, "games": orjson.Fragment(payload)}))
    except OSError as exc:
        logger.warning(f"Snapshot file write failed: {exc}")
    try:
        redis = await get_redis()
        await redis.setex("odds:all", ODDS_TTL, payload)
        await redis.setex("odds:polled_at", ODDS_TTL, polled_at)
    except Exception as exc:
        logger.warning(f"Redis persist failed: {exc}")


async def warm_start() -> None:
    """Load the last snapshot (Redis first, then the local file) so a restart starts with data."""
    raw = polled_at = None
    try:
        redis = await get_redis()
        raw = await redis.get("odds:all")
        polled_at = await redis.get("odds:polled_at")
    except Exception as exc:
        logger.warning(f"Redis unavailable for warm start: {exc}")
    if raw:
        store.update(orjson.loads(raw), polled_at)
        return
    if SNAPSHOT_FILE.exists():
        try:
            snap = orjson.loads(SNAPSHOT_FILE.read_bytes())
        except (OSError, orjson.JSONDecodeError) as exc:
            logger.warning(f"Snapshot file unreadable: {exc}")
            return
        store.update(snap["games"], snap["polled_at"])
        logger.info(f"Warm start from {SNAPSHOT_FILE.name} (polled {snap['polled_at']})")


def snapshot_age_seconds() -> float | None:
    if not store.polled_at:
        return None
    return time.time() - datetime.fromisoformat(store.polled_at).timestamp()

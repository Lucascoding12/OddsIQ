"""
Arb endpoints.

GET /arb/opportunities — returns the latest scanned arb opportunities from Redis.
The actual scanning happens in services/arb_scanner.py, triggered by APScheduler.
"""
import json
from fastapi import APIRouter, Query

router = APIRouter(tags=["arb"])


@router.get("/arb/opportunities")
async def get_arb_opportunities(
    sport_key: str | None = Query(None, description="Filter by Odds API sport key"),
    min_profit_pct: float = Query(0.0, ge=0),
):
    """Return arb opportunities from Redis cache. Empty list if scanner hasn't run yet."""
    from services.redis_client import get_redis

    redis = await get_redis()
    raw = await redis.get("arb:opportunities")
    if not raw:
        return []

    opportunities: list[dict] = json.loads(raw)

    if sport_key:
        opportunities = [o for o in opportunities if o.get("sport_key") == sport_key]
    if min_profit_pct > 0:
        opportunities = [o for o in opportunities if o.get("profit_pct", 0) >= min_profit_pct]

    return opportunities

"""
Arb endpoints.

GET /arb/opportunities — returns the latest scanned arb opportunities from Redis.
The actual scanning happens in services/arb_scanner.py, triggered by APScheduler.
"""
from fastapi import APIRouter, Query, Response

from services import odds_cache

router = APIRouter(tags=["arb"])


@router.get("/arb/opportunities")
async def get_arb_opportunities(
    response: Response,
    sport_key: str | None = Query(None, description="Filter by Odds API sport key"),
    min_profit_pct: float = Query(0.0, ge=0),
):
    """Return arb opportunities from Redis cache. Empty list if scanner hasn't run yet."""
    opportunities: list[dict] = await odds_cache.get_json("arb:opportunities") or []

    if sport_key:
        opportunities = [o for o in opportunities if o.get("sport_key") == sport_key]
    if min_profit_pct > 0:
        opportunities = [o for o in opportunities if o.get("profit_pct", 0) >= min_profit_pct]

    response.headers["Cache-Control"] = "public, max-age=30"
    return opportunities

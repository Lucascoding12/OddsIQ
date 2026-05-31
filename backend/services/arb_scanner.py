"""
Arbitrage scanner — reads cached odds from Redis and finds 2-way arb opportunities.

Formula:
  implied_prob = 1 / decimal_odds
  arb exists when: sum(1 / best_odds_per_outcome) < 1.0

For American odds → decimal:
  positive: decimal = (odds / 100) + 1
  negative: decimal = (100 / abs(odds)) + 1

Results are cached back to Redis under 'arb:opportunities'.
"""
import json
import logging
from dataclasses import dataclass, asdict

from services.redis_client import get_redis, ARB_TTL

logger = logging.getLogger(__name__)


def american_to_decimal(american: float) -> float:
    if american > 0:
        return (american / 100) + 1
    return (100 / abs(american)) + 1


def implied_prob(american: float) -> float:
    return 1 / american_to_decimal(american)


@dataclass
class ArbLeg:
    book: str
    outcome: str
    odds: int  # American
    stake: float  # calculated for $100 profit
    payout: float


@dataclass
class ArbOpportunity:
    game_id: str
    sport_key: str
    home_team: str
    away_team: str
    commence_time: str
    legs: list[ArbLeg]
    profit_pct: float  # guaranteed profit as % of total stake
    total_stake: float


def find_arb_in_game(game: dict) -> ArbOpportunity | None:
    """
    Given a game dict from The Odds API, find the best odds per outcome
    across all bookmakers and check if an arb exists.
    """
    bookmakers = game.get("bookmakers", [])
    if not bookmakers:
        return None

    # Collect best odds per outcome: {outcome_name: (odds_value, book_name)}
    best: dict[str, tuple[int, str]] = {}

    for book in bookmakers:
        for market in book.get("markets", []):
            if market.get("key") != "h2h":
                continue
            for outcome in market.get("outcomes", []):
                name = outcome["name"]
                price = outcome["price"]
                if name not in best or price > best[name][0]:
                    best[name] = (price, book["key"])

    if len(best) != 2:
        # Only handle 2-way markets (no draws/3-way)
        return None

    outcomes = list(best.items())
    total_implied = sum(implied_prob(o[1][0]) for o in outcomes)

    if total_implied >= 1.0:
        return None  # No arb

    profit_pct = round((1 - total_implied) * 100, 3)

    # Calculate stakes for $100 total profit
    legs = []
    total_stake = 0.0
    for name, (odds, book) in outcomes:
        dec = american_to_decimal(odds)
        # Stake proportional to implied prob so each leg wins the same amount
        stake = round((implied_prob(odds) / total_implied) * 100, 2)
        payout = round(stake * dec, 2)
        total_stake += stake
        legs.append(ArbLeg(book=book, outcome=name, odds=odds, stake=stake, payout=payout))

    return ArbOpportunity(
        game_id=game["id"],
        sport_key=game["sport_key"],
        home_team=game["home_team"],
        away_team=game["away_team"],
        commence_time=game.get("commence_time", ""),
        legs=legs,
        profit_pct=profit_pct,
        total_stake=round(total_stake, 2),
    )


async def scan_for_arb() -> list[dict]:
    """
    Read all cached games from Redis, scan for arb, cache results.
    Returns the list of opportunities as dicts.
    """
    redis = await get_redis()
    raw = await redis.get("odds:all")
    if not raw:
        logger.info("Arb scan: no odds in cache yet")
        return []

    games: list[dict] = json.loads(raw)
    opportunities: list[dict] = []

    for game in games:
        opp = find_arb_in_game(game)
        if opp:
            opportunities.append(asdict(opp))

    # Sort by profit % descending
    opportunities.sort(key=lambda x: x["profit_pct"], reverse=True)

    await redis.setex("arb:opportunities", ARB_TTL, json.dumps(opportunities))
    logger.info(f"Arb scan: {len(opportunities)} opportunities found from {len(games)} games")
    return opportunities

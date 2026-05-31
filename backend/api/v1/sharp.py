"""
Sharp metrics endpoints.

Derives signals from live odds in Redis:

1. /sharp/line-movement
   - For each game, compares best odds vs worst odds per outcome across books.
   - A big gap (>15 cents/points) between best and worst indicates books are
     disagreeing — usually means sharp money has already moved some books
     while others haven't caught up. We flag this as a "steam" signal.
   - "open" = worst available odds on that outcome (lagging book)
   - "current" = best available odds (sharp-adjusted book)

2. /sharp/consensus
   - Returns implied probability spread across books for each game outcome.
   - High variance = market disagreement / potential edge.

True open-to-close CLV requires storing historical snapshots (OddsSnapshot table).
That's populated once the poller writes to Postgres (Phase 2 of the plan).
For now, consensus and disparity are computed live from Redis.
"""
import json
import statistics
from fastapi import APIRouter

router = APIRouter(tags=["sharp"])


def american_to_decimal(odds: float) -> float:
    if odds > 0:
        return odds / 100 + 1
    return 100 / abs(odds) + 1


def implied_prob(odds: float) -> float:
    return 1 / american_to_decimal(odds)


def no_vig_prob(odds_a: float, odds_b: float) -> tuple[float, float]:
    """Remove the vig from a 2-way market, return fair implied probs."""
    p_a = implied_prob(odds_a)
    p_b = implied_prob(odds_b)
    total = p_a + p_b
    return p_a / total, p_b / total


@router.get("/sharp/line-movement")
async def get_line_movement(limit: int = 30):
    """
    Return games with the most book disagreement on h2h odds.
    Sorted by disparity (largest spread between best and worst odds per outcome).
    Acts as a proxy for line movement and steam detection.
    """
    from services.redis_client import get_redis

    redis = await get_redis()
    raw = await redis.get("odds:all")
    if not raw:
        return []

    games: list[dict] = json.loads(raw)
    results = []

    for game in games:
        bookmakers = game.get("bookmakers", [])
        home = game.get("home_team", "")
        away = game.get("away_team", "")

        # Collect all h2h prices per outcome
        prices: dict[str, list[tuple[str, int]]] = {}
        for book in bookmakers:
            for market in book.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                for outcome in market.get("outcomes", []):
                    name = outcome["name"]
                    price = outcome["price"]
                    prices.setdefault(name, []).append((book.get("title", book.get("key")), price))

        if len(prices) != 2:
            continue  # skip 3-way markets

        outcomes = list(prices.keys())
        for outcome_name in outcomes:
            book_prices = prices[outcome_name]
            if len(book_prices) < 2:
                continue

            odds_vals = [p for _, p in book_prices]
            best_odds = max(odds_vals)
            worst_odds = min(odds_vals)
            best_book = next(b for b, p in book_prices if p == best_odds)
            worst_book = next(b for b, p in book_prices if p == worst_odds)

            # Disparity in implied probability points (book disagreement)
            disparity = abs(implied_prob(worst_odds) - implied_prob(best_odds))

            # Steam flag: >8% implied prob gap between best and worst book
            steam = disparity > 0.08

            if disparity > 0.02:  # only surface meaningful gaps
                results.append({
                    "game": f"{away} @ {home}",
                    "sport_key": game.get("sport_key"),
                    "commence_time": game.get("commence_time"),
                    "outcome": outcome_name,
                    "betType": "Moneyline",
                    "worstOdds": worst_odds,
                    "worstBook": worst_book,
                    "bestOdds": best_odds,
                    "bestBook": best_book,
                    "disparityPct": round(disparity * 100, 2),
                    "steamFlag": steam,
                    "bookCount": len(book_prices),
                })

    # Sort by largest disagreement first
    results.sort(key=lambda x: x["disparityPct"], reverse=True)
    return results[:limit]


@router.get("/sharp/no-vig")
async def get_no_vig_odds(limit: int = 30):
    """
    Return no-vig (fair) odds for each game by removing the bookmaker margin.
    Useful for identifying when a book's price is above or below the true line.
    """
    from services.redis_client import get_redis

    redis = await get_redis()
    raw = await redis.get("odds:all")
    if not raw:
        return []

    games: list[dict] = json.loads(raw)
    results = []

    for game in games:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        bookmakers = game.get("bookmakers", [])

        book_lines = []
        for book in bookmakers:
            for market in book.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                home_odds = outcomes.get(home)
                away_odds = outcomes.get(away)
                if home_odds and away_odds:
                    fair_home, fair_away = no_vig_prob(home_odds, away_odds)
                    vig = (implied_prob(home_odds) + implied_prob(away_odds) - 1) * 100
                    book_lines.append({
                        "book": book.get("title", book.get("key")),
                        "homeOdds": home_odds,
                        "awayOdds": away_odds,
                        "fairHomeProb": round(fair_home * 100, 2),
                        "fairAwayProb": round(fair_away * 100, 2),
                        "vigPct": round(vig, 3),
                    })

        if book_lines:
            # Consensus fair probability = average across all books
            avg_home = statistics.mean(b["fairHomeProb"] for b in book_lines)
            avg_away = statistics.mean(b["fairAwayProb"] for b in book_lines)
            avg_vig = statistics.mean(b["vigPct"] for b in book_lines)

            results.append({
                "game": f"{away} @ {home}",
                "sport_key": game.get("sport_key"),
                "home_team": home,
                "away_team": away,
                "commence_time": game.get("commence_time"),
                "consensusFairHomeProb": round(avg_home, 2),
                "consensusFairAwayProb": round(avg_away, 2),
                "avgVigPct": round(avg_vig, 3),
                "books": book_lines,
            })

    return results[:limit]

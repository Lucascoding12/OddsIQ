from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(tags=["arb"])


class ArbLeg(BaseModel):
    book: str
    odds: int          # American
    impliedProb: float # 0–1


class ArbOpportunity(BaseModel):
    id: str
    sport: str
    category: str
    homeTeam: str
    awayTeam: str
    commenceTime: str
    betType: str       # e.g. "Moneyline", "Spread", "Total"
    legs: list[ArbLeg]
    totalImpliedProb: float   # < 1.0 means arb exists
    profitPct: float          # guaranteed ROI %
    detectedAt: str           # ISO timestamp


def american_to_decimal(odds: int) -> float:
    if odds > 0:
        return odds / 100 + 1
    return 100 / abs(odds) + 1


def scan_for_arb(games: list) -> list[ArbOpportunity]:
    """
    Scan a list of games (each with bookmaker odds per market) and return
    any opportunities where total implied probability < 1.0.

    games is expected to be the raw Odds API response format:
    [
      {
        "id": ..., "sport_key": ..., "home_team": ..., "away_team": ...,
        "commence_time": ...,
        "bookmakers": [
          { "key": ..., "title": ..., "markets": [
            { "key": "h2h", "outcomes": [
              { "name": ..., "price": <american odds int> }, ...
            ]}
          ]}
        ]
      }, ...
    ]
    """
    opportunities: list[ArbOpportunity] = []
    opp_id = 0

    for game in games:
        # Index: market_key → outcome_name → list of (book_title, american_odds)
        market_lines: dict[str, dict[str, list[tuple[str, int]]]] = {}

        for bookmaker in game.get("bookmakers", []):
            title = bookmaker["title"]
            for market in bookmaker.get("markets", []):
                mkey = market["key"]
                if mkey not in market_lines:
                    market_lines[mkey] = {}
                for outcome in market.get("outcomes", []):
                    name = outcome["name"]
                    price = outcome["price"]
                    market_lines[mkey].setdefault(name, []).append((title, price))

        for mkey, outcomes in market_lines.items():
            outcome_names = list(outcomes.keys())
            if len(outcome_names) != 2:
                # Only scan 2-way markets (skip 3-way soccer h2h etc.)
                continue

            # Best odds for each side across all books
            best: list[tuple[str, int]] = []
            for name in outcome_names:
                lines = outcomes[name]
                # Pick the book offering the highest (most favorable) odds
                best_book, best_price = max(lines, key=lambda x: american_to_decimal(x[1]))
                best.append((best_book, best_price))

            decimals = [american_to_decimal(p) for _, p in best]
            implied = sum(1 / d for d in decimals)

            if implied < 1.0:
                opp_id += 1
                legs = [
                    ArbLeg(
                        book=best[i][0],
                        odds=best[i][1],
                        impliedProb=round(1 / decimals[i], 6),
                    )
                    for i in range(len(best))
                ]
                bet_type = {"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"}.get(mkey, mkey)
                opportunities.append(
                    ArbOpportunity(
                        id=str(opp_id),
                        sport=game.get("sport_key", ""),
                        category=game.get("sport_title", ""),
                        homeTeam=game.get("home_team", ""),
                        awayTeam=game.get("away_team", ""),
                        commenceTime=game.get("commence_time", ""),
                        betType=bet_type,
                        legs=legs,
                        totalImpliedProb=round(implied, 6),
                        profitPct=round((1 / implied - 1) * 100, 4),
                        detectedAt=datetime.utcnow().isoformat() + "Z",
                    )
                )

    return sorted(opportunities, key=lambda o: o.profitPct, reverse=True)


# In-memory store — replaced by Redis/DB once the odds poller is wired up
_latest_opportunities: list[ArbOpportunity] = []


@router.get("/arb/opportunities", response_model=list[ArbOpportunity])
def get_arb_opportunities(sport: str | None = None, min_profit_pct: float = 0.0):
    """Return the most recently scanned arb opportunities, sorted by profit %."""
    results = _latest_opportunities
    if sport:
        results = [o for o in results if o.sport == sport or o.category == sport]
    if min_profit_pct > 0:
        results = [o for o in results if o.profitPct >= min_profit_pct]
    return results

"""
Odds endpoints.

GET /odds          — all cached games (optionally filtered by sport_key or category)
GET /odds/sports   — the full sport category tree
GET /odds/arb-eligible — sports eligible for 2-way arb scanning
"""
import json
from fastapi import APIRouter, Query, Response

from services import odds_cache

router = APIRouter(tags=["odds"])

# Odds only change when the poller runs (every few hours in prod), so letting
# the browser reuse a response for 30s costs nothing in freshness and makes
# page/filter switches instant.
CACHE_CONTROL = "public, max-age=30"

# Maps display sport name → The Odds API sport_key
SPORT_KEYS: dict[str, str] = {
    # American Football
    "NFL": "americanfootball_nfl",
    "NFL Preseason": "americanfootball_nfl_preseason",
    "NCAAF": "americanfootball_ncaaf",
    "CFL": "americanfootball_cfl",
    "UFL": "americanfootball_ufl",
    # Basketball
    "NBA": "basketball_nba",
    "WNBA": "basketball_wnba",
    "NCAAB": "basketball_ncaab",
    "NCAAW": "basketball_ncaaw",
    "EuroLeague": "basketball_euroleague",
    "NBA Summer League": "basketball_nba_summer_league",
    # Baseball
    "MLB": "baseball_mlb",
    "MLB Preseason": "baseball_mlb_preseason",
    "NCAA Baseball": "baseball_ncaa",
    "MiLB": "baseball_milb",
    "NPB": "baseball_npb",
    "KBO": "baseball_kbo",
    # Hockey
    "NHL": "icehockey_nhl",
    "AHL": "icehockey_ahl",
    "SHL": "icehockey_sweden_hockey_league",
    "HockeyAllsvenskan": "icehockey_sweden_allsvenskan",
    "Liiga": "icehockey_liiga",
    "Mestis": "icehockey_mestis",
    # Soccer
    "EPL": "soccer_epl",
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "La Liga": "soccer_spain_la_liga",
    "Bundesliga": "soccer_germany_bundesliga",
    "Serie A": "soccer_italy_serie_a",
    "Ligue 1": "soccer_france_ligue_one",
    "MLS": "soccer_usa_mls",
    "EFL Championship": "soccer_efl_champ",
    "Liga MX": "soccer_mexico_ligamx",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "Brazilian Serie A": "soccer_brazil_campeonato",
    "A-League": "soccer_australia_aleague",
    # Tennis
    "ATP Tour": "tennis_atp_french_open",
    "WTA Tour": "tennis_wta_french_open",
    "Grand Slams": "tennis_atp_us_open",
    "Challenger": "tennis_atp_challenger",
    # Combat Sports
    "UFC": "mma_ufc",
    "MMA": "mma_mixed_martial_arts",
    "Boxing": "boxing_boxing",
    # Cricket
    "IPL": "cricket_ipl",
    "Big Bash": "cricket_big_bash",
    "Test Cricket": "cricket_test_match",
    "International Cricket": "cricket_international_t20",
    # Rugby
    "NRL": "rugbyleague_nrl",
    "Rugby Union": "rugbyunion_world_cup",
    # Golf
    "PGA Tour": "golf_pga_championship",
    "Masters": "golf_masters_tournament",
    "US Open Golf": "golf_us_open",
    "The Open Championship": "golf_the_open_championship",
    # Motorsports
    "Formula 1": "motorsport_formula_one",
    # Esports
    "Esports": "esports_lol_world_championship",
    # Politics & Specials
    "US Politics": "politics_us_presidential_election_winner",
    "Special Markets": "politics_us_presidential_election_winner",
}

# Reverse map: sport_key → display name
SPORT_KEY_TO_NAME: dict[str, str] = {v: k for k, v in SPORT_KEYS.items()}

SPORT_CATEGORIES: dict[str, list[str]] = {
    "American Football": ["NFL", "NFL Preseason", "NCAAF", "CFL", "UFL"],
    "Basketball": ["NBA", "WNBA", "NCAAB", "NCAAW", "EuroLeague", "NBA Summer League"],
    "Baseball": ["MLB", "MLB Preseason", "NCAA Baseball", "MiLB", "NPB", "KBO"],
    "Hockey": ["NHL", "AHL", "SHL", "HockeyAllsvenskan", "Liiga", "Mestis"],
    "Soccer": ["EPL", "Champions League", "Europa League", "La Liga", "Bundesliga", "Serie A",
               "Ligue 1", "MLS", "EFL Championship", "Liga MX", "Eredivisie", "Brazilian Serie A", "A-League"],
    "Tennis": ["ATP Tour", "WTA Tour", "Grand Slams", "Challenger"],
    "Combat Sports": ["UFC", "MMA", "Boxing"],
    "Cricket": ["IPL", "Big Bash", "Test Cricket", "International Cricket"],
    "Rugby": ["NRL", "Rugby Union"],
    "Golf": ["PGA Tour", "Masters", "US Open Golf", "The Open Championship"],
    "Motorsports": ["Formula 1"],
    "Esports": ["Esports"],
    "Politics & Specials": ["US Politics", "Special Markets"],
}

# Build reverse: sport_key → category name
_SPORT_TO_CATEGORY: dict[str, str] = {}
for _cat, _sports in SPORT_CATEGORIES.items():
    for _s in _sports:
        if _s in SPORT_KEYS:
            _SPORT_TO_CATEGORY[SPORT_KEYS[_s]] = _cat

# 2-way moneyline sports only (safe for arb scanning — no draws)
ARB_ELIGIBLE_SPORTS: set[str] = {
    "NFL", "NFL Preseason", "NCAAF", "CFL", "UFL",
    "NBA", "WNBA", "NCAAB", "NCAAW", "EuroLeague", "NBA Summer League",
    "MLB", "MLB Preseason", "NCAA Baseball", "MiLB", "NPB", "KBO",
    "NHL", "AHL", "SHL", "HockeyAllsvenskan", "Liiga", "Mestis",
    "ATP Tour", "WTA Tour", "Grand Slams", "Challenger",
    "UFC", "MMA", "Boxing",
    "NRL",
    "Esports",
}


def _normalize_game(raw: dict) -> dict:
    """
    Convert a raw Odds API game dict to the shape the frontend expects.
    Picks the best moneyline odds across all bookmakers.
    """
    sport_key = raw.get("sport_key", "")
    sport_name = SPORT_KEY_TO_NAME.get(sport_key, sport_key)
    category = _SPORT_TO_CATEGORY.get(sport_key, "Other")

    # Find best h2h odds per outcome independently across all books.
    # Best home = highest home price (most favorable for home bettors).
    # Best away = highest away price (most favorable for away bettors).
    # Best book = book with lowest combined implied probability (least vig / best value).
    best_home: int | None = None
    best_away: int | None = None
    best_book = ""
    lowest_vig: float | None = None

    def _american_to_implied(price: int | float) -> float:
        if price > 0:
            return 100 / (price + 100)
        return abs(price) / (abs(price) + 100)

    for book in raw.get("bookmakers", []):
        for market in book.get("markets", []):
            if market.get("key") != "h2h":
                continue
            outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
            home_odds = outcomes.get(raw.get("home_team", ""))
            away_odds = outcomes.get(raw.get("away_team", ""))
            if home_odds is None or away_odds is None:
                continue

            # Track best home and away independently
            if best_home is None or home_odds > best_home:
                best_home = home_odds
            if best_away is None or away_odds > best_away:
                best_away = away_odds

            # Best book = lowest total implied prob (least vig)
            total_implied = _american_to_implied(home_odds) + _american_to_implied(away_odds)
            if lowest_vig is None or total_implied < lowest_vig:
                lowest_vig = total_implied
                best_book = book.get("title", book.get("key", ""))

    return {
        "id": raw.get("id"),
        "sport": sport_name,
        "sportKey": sport_key,
        "category": category,
        "homeTeam": raw.get("home_team"),
        "awayTeam": raw.get("away_team"),
        "commenceTime": raw.get("commence_time"),
        "polledAt": raw.get("polled_at"),
        "bestLine": {
            "homeMoneyline": best_home,
            "awayMoneyline": best_away,
            "book": best_book,
        },
        "bookmakers": raw.get("bookmakers", []),
    }


@router.get("/odds")
async def get_odds(
    sport: str | None = Query(None, description="Filter by display name, e.g. 'NFL'"),
    sport_key: str | None = Query(None, description="Filter by Odds API key, e.g. 'americanfootball_nfl'"),
    category: str | None = Query(None, description="Filter by category, e.g. 'Basketball'"),
):
    """Return live odds from Redis cache. Empty list if not yet polled."""
    # Try sport-specific key first (cheaper), fall back to all
    if sport_key:
        key = f"odds:sport:{sport_key}"
    elif sport and sport in SPORT_KEYS:
        key = f"odds:sport:{SPORT_KEYS[sport]}"
    else:
        key = "odds:all"

    def compute(games: list[dict]) -> str:
        normalized = [_normalize_game(g) for g in games]
        if category:
            normalized = [g for g in normalized if g["category"] == category]
        return json.dumps(normalized)

    # Normalization + serialization are memoized per payload, so repeat
    # requests between polls skip both the parse and the dumps entirely.
    payload = await odds_cache.get_derived(key, f"normalized:{category or 'all'}", compute)
    return Response(
        content=payload or "[]",
        media_type="application/json",
        headers={"Cache-Control": CACHE_CONTROL},
    )


@router.get("/odds/sports", response_model=dict[str, list[str]])
def get_sport_categories(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return SPORT_CATEGORIES


@router.get("/odds/arb-eligible", response_model=list[str])
def get_arb_eligible_sports(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return sorted(ARB_ELIGIBLE_SPORTS)

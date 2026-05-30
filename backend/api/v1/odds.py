from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(tags=["odds"])

# Maps display sport name → The Odds API sport_key
# https://the-odds-api.com/sports-odds-data/sports-apis.html
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

# 2-way moneyline sports (safe for arb scanning)
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


class BestLine(BaseModel):
    homeMoneyline: int
    awayMoneyline: int
    spread: float
    spreadOdds: int
    total: float
    overOdds: int
    underOdds: int
    book: str


class Game(BaseModel):
    id: str
    sport: str
    sportKey: str
    category: str
    homeTeam: str
    awayTeam: str
    commenceTime: str
    bestLine: BestLine


@router.get("/odds", response_model=list[Game])
def get_odds(
    sport: str | None = Query(None, description="Filter by display sport name, e.g. 'NFL'"),
    category: str | None = Query(None, description="Filter by category, e.g. 'Basketball'"),
):
    # No live data yet — returns empty until odds poller is wired up
    return []


@router.get("/odds/sports", response_model=dict[str, list[str]])
def get_sport_categories():
    return SPORT_CATEGORIES


@router.get("/odds/arb-eligible", response_model=list[str])
def get_arb_eligible_sports():
    return sorted(ARB_ELIGIBLE_SPORTS)

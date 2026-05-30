from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["odds"])

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
    homeTeam: str
    awayTeam: str
    commenceTime: str
    bestLine: BestLine

MOCK_GAMES = [
    Game(id="1", sport="NFL", homeTeam="Kansas City Chiefs", awayTeam="Buffalo Bills",
         commenceTime="2026-09-10T20:20:00Z",
         bestLine=BestLine(homeMoneyline=-150, awayMoneyline=130, spread=-3, spreadOdds=-110,
                           total=47.5, overOdds=-110, underOdds=-110, book="DraftKings")),
]

@router.get("/odds", response_model=list[Game])
def get_odds(sport: str | None = None):
    if sport:
        return [g for g in MOCK_GAMES if g.sport == sport]
    return MOCK_GAMES

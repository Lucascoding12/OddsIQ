from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["bets"])

class BetCreate(BaseModel):
    date: str
    sport: str
    game: str
    betType: str
    odds: int
    stake: float
    result: str

class Bet(BetCreate):
    id: str
    pnl: float
    closingOdds: int
    clv: float

_bets: list[Bet] = []

@router.get("/bets", response_model=list[Bet])
def list_bets():
    return _bets

@router.post("/bets", response_model=Bet, status_code=201)
def create_bet(body: BetCreate):
    bet = Bet(id=str(len(_bets) + 1), pnl=0.0, closingOdds=body.odds, clv=0.0, **body.model_dump())
    _bets.append(bet)
    return bet

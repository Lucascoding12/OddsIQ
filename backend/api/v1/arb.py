from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["arb"])

class ArbRequest(BaseModel):
    leg1Odds: int
    leg2Odds: int
    totalStake: float

class ArbResult(BaseModel):
    impliedProb: float
    isArb: bool
    stake1: float
    stake2: float
    profit: float

def american_to_decimal(odds: int) -> float:
    if odds > 0:
        return odds / 100 + 1
    return 100 / abs(odds) + 1

@router.post("/arb/calculate", response_model=ArbResult)
def calculate_arb(body: ArbRequest):
    d1 = american_to_decimal(body.leg1Odds)
    d2 = american_to_decimal(body.leg2Odds)
    implied = 1 / d1 + 1 / d2
    is_arb = implied < 1
    stake1 = (body.totalStake / d1) / implied
    stake2 = (body.totalStake / d2) / implied
    profit = body.totalStake * (1 / implied - 1) if is_arb else 0
    return ArbResult(impliedProb=implied, isArb=is_arb, stake1=stake1, stake2=stake2, profit=profit)

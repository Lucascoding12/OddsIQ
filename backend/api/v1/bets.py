"""
Bets endpoints — user PnL tracking.

Multi-user isolation via X-User-Email header.
The frontend sends the logged-in user's email with every request.
Bets are filtered to that email so each user only sees their own data.
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import Bet as BetModel

router = APIRouter(tags=["bets"])

DEFAULT_USER = "anonymous"


def _get_user(x_user_email: str | None = Header(default=None)) -> str:
    """Extract user identity from header. Falls back to 'anonymous'."""
    return (x_user_email or DEFAULT_USER).strip().lower()


class BetCreate(BaseModel):
    date: str
    sport: str
    game: str
    betType: str
    odds: float
    stake: float
    result: str = "pending"
    pnl: float = 0.0


class BetOut(BaseModel):
    id: int
    date: str
    sport: str
    game: str
    betType: str
    odds: float
    stake: float
    result: str
    pnl: float
    closingOdds: float | None = None
    clv: float | None = None

    model_config = {"from_attributes": True}


def _to_out(bet: BetModel) -> BetOut:
    return BetOut(
        id=bet.id,
        date=bet.date,
        sport=bet.sport,
        game=bet.game,
        betType=bet.bet_type,
        odds=bet.odds,
        stake=bet.stake,
        result=bet.result,
        pnl=bet.pnl,
        closingOdds=bet.closing_odds,
        clv=bet.clv,
    )


@router.get("/bets", response_model=list[BetOut])
async def list_bets(
    user: str = Depends(_get_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BetModel)
        .where(BetModel.user_email == user)
        .order_by(BetModel.created_at.desc())
    )
    return [_to_out(b) for b in result.scalars().all()]


@router.post("/bets", response_model=BetOut, status_code=201)
async def create_bet(
    body: BetCreate,
    user: str = Depends(_get_user),
    db: AsyncSession = Depends(get_db),
):
    bet = BetModel(
        user_email=user,
        date=body.date,
        sport=body.sport,
        game=body.game,
        bet_type=body.betType,
        odds=body.odds,
        stake=body.stake,
        result=body.result,
        pnl=body.pnl,
    )
    db.add(bet)
    await db.commit()
    await db.refresh(bet)
    return _to_out(bet)


@router.patch("/bets/{bet_id}", response_model=BetOut)
async def update_bet(
    bet_id: int,
    body: BetCreate,
    user: str = Depends(_get_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BetModel).where(BetModel.id == bet_id, BetModel.user_email == user)
    )
    bet = result.scalar_one_or_none()
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    bet.result = body.result
    bet.pnl = body.pnl
    await db.commit()
    await db.refresh(bet)
    return _to_out(bet)


@router.delete("/bets/{bet_id}", status_code=204)
async def delete_bet(
    bet_id: int,
    user: str = Depends(_get_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BetModel).where(BetModel.id == bet_id, BetModel.user_email == user)
    )
    bet = result.scalar_one_or_none()
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    await db.delete(bet)
    await db.commit()

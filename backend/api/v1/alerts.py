"""
Alerts endpoints — user price alerts stored in Postgres.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import Alert as AlertModel

router = APIRouter(tags=["alerts"])


class AlertCreate(BaseModel):
    sport: str
    team: str
    market: str = "h2h"
    targetOdds: float
    direction: str = "above"  # above | below
    note: str = ""


class AlertOut(BaseModel):
    id: int
    sport: str
    team: str
    market: str
    targetOdds: float
    direction: str
    active: bool
    note: str

    model_config = {"from_attributes": True}


def _to_out(a: AlertModel) -> AlertOut:
    return AlertOut(
        id=a.id,
        sport=a.sport,
        team=a.team,
        market=a.market,
        targetOdds=a.target_odds,
        direction=a.direction,
        active=a.active,
        note=a.note,
    )


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertModel).order_by(AlertModel.created_at.desc()))
    return [_to_out(a) for a in result.scalars().all()]


@router.post("/alerts", response_model=AlertOut, status_code=201)
async def create_alert(body: AlertCreate, db: AsyncSession = Depends(get_db)):
    alert = AlertModel(
        sport=body.sport,
        team=body.team,
        market=body.market,
        target_odds=body.targetOdds,
        direction=body.direction,
        note=body.note,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return _to_out(alert)


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertModel).where(AlertModel.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()

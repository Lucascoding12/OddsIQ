from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["alerts"])

class AlertCreate(BaseModel):
    game: str
    betType: str
    targetOdds: int
    book: str

class Alert(AlertCreate):
    id: str
    status: str
    createdAt: str

_alerts: list[Alert] = []

@router.get("/alerts", response_model=list[Alert])
def list_alerts():
    return _alerts

@router.post("/alerts", response_model=Alert, status_code=201)
def create_alert(body: AlertCreate):
    alert = Alert(id=str(len(_alerts) + 1), status="active", createdAt="2026-05-29", **body.model_dump())
    _alerts.append(alert)
    return alert

@router.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(alert_id: str):
    global _alerts
    _alerts = [a for a in _alerts if a.id != alert_id]

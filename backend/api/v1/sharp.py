from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["sharp"])

class LineMovement(BaseModel):
    game: str
    betType: str
    openLine: float
    currentLine: float
    book: str
    steamFlag: bool

@router.get("/sharp/line-movement", response_model=list[LineMovement])
def get_line_movement():
    return [
        LineMovement(game="Chiefs vs Bills", betType="Spread", openLine=-2.5, currentLine=-3.5, book="Pinnacle", steamFlag=True),
        LineMovement(game="Celtics vs Lakers", betType="ML", openLine=-185, currentLine=-200, book="DraftKings", steamFlag=False),
    ]

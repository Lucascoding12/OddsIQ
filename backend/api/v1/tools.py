"""
JSON endpoints for line shopping, sharp metrics and calculators — the same
data the server-rendered pages show, for the Next.js app or scripts.
"""
import dataclasses

from fastapi import APIRouter, HTTPException, Query

from services import calculators, line_shop, sharp_metrics
from services.odds_store import store

router = APIRouter(tags=["tools"])


@router.get("/shop")
async def shop(q: str = Query(..., min_length=1, max_length=100)) -> list[dict]:
    """Every book's price for a searched bet, best first. e.g. ?q=chiefs -3.5"""
    return store.memo(("shop-json", q.strip()), lambda: line_shop.search(store.grouped, q.strip()))


def sharp_summary(sport_key: str | None = None, limit: int = 25) -> dict:
    """Every sharp metric for the current snapshot, optionally for one sport."""
    def compute() -> dict:
        grouped = [gm for gm in store.grouped if not sport_key or gm.game.get("sport_key") == sport_key]
        return {
            "sharp_public": sharp_metrics.sharp_vs_public(grouped)[:limit],
            "moves": store.moves.moves(grouped)[:limit],
            "disagreement": sharp_metrics.disagreement(grouped)[:limit],
            "holds": sharp_metrics.book_holds(grouped),
            "tracking_since": store.moves.since,
        }

    return store.memo(("sharp", sport_key, limit), compute)


@router.get("/sharp/summary")
async def get_sharp_summary(sport_key: str | None = None, limit: int = Query(25, ge=1, le=200)) -> dict:
    return sharp_summary(sport_key, limit)


@router.get("/calc")
async def list_calculators() -> list[dict]:
    return [
        {"slug": c.slug, "name": c.name, "description": c.description,
         "fields": [dataclasses.asdict(f) for f in c.fields]}
        for c in calculators.CALCULATORS
    ]


@router.post("/calc/{slug}")
async def post_calculator(slug: str, body: dict[str, str]) -> dict:
    calc = calculators.BY_SLUG.get(slug)
    if calc is None:
        raise HTTPException(404, detail=f"Unknown calculator '{slug}'")
    result, error = calculators.run(calc, body)
    if error:
        raise HTTPException(422, detail=error)
    return dataclasses.asdict(result)

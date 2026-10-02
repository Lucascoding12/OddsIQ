"""
+EV endpoints.

GET /ev — soft-book prices that beat the sharp-book fair line.

The scan runs once per poll in the store; requests only filter by book,
re-sort, and size Kelly stakes for the caller's bankroll.
"""
from dataclasses import dataclass

import orjson
from fastapi import APIRouter, Depends, Query, Response

from services.ev_engine import CROSS_CHECKS, REFERENCE_PRIORITY, ev_payload
from services.odds_store import store

router = APIRouter(tags=["ev"])

CONFIDENCE_RANK = {"thin": 0, "fair": 1, "strong": 2}


@dataclass(frozen=True)
class EvQuery:
    sport_key: str | None
    market: str | None
    min_ev_pct: float
    min_prob: float
    books: frozenset[str] | None
    bankroll: float
    kelly: float
    round_to: float
    sort: str
    hide_suspicious: bool
    min_sharps: int
    min_confidence: str = "thin"


def ev_query(
    sport_key: str | None = Query(None),
    market: str | None = Query(None, pattern="^(h2h|spreads|totals)$"),
    min_ev_pct: float = Query(1.0, ge=0, description="Minimum edge over the sharp fair line, %"),
    min_prob: float = Query(0.0, ge=0, le=1, description="Minimum fair win probability, 0–1"),
    books: str | None = Query(None, description="Comma-separated book keys you can bet at"),
    bankroll: float = Query(1000.0, gt=0, le=10_000_000),
    kelly: float = Query(0.25, gt=0, le=1, description="Fraction of full Kelly to stake"),
    round_to: float = Query(1.0, ge=0),
    sort: str = Query("edge", pattern="^(edge|likely)$", description="edge = biggest EV, likely = highest win probability"),
    hide_suspicious: bool = Query(False),
    min_sharps: int = Query(1, ge=1, le=5, description="Require the fair line from at least this many sharp books"),
    min_confidence: str = Query("fair", pattern="^(thin|fair|strong)$",
                                description="strong = 3+ sharp sources all agree it's +EV; fair = 2+; thin = anything"),
) -> EvQuery:
    book_set = frozenset(b.strip() for b in books.split(",") if b.strip()) if books else None
    return EvQuery(sport_key, market, min_ev_pct, min_prob, book_set or None, bankroll, kelly, round_to, sort, hide_suspicious, min_sharps, min_confidence)


def select_ev(q: EvQuery) -> list[dict]:
    def compute() -> list[dict]:
        out = []
        for bet in store.ev_bets:
            if bet.fair_prob < q.min_prob or len(bet.sharp_books) < q.min_sharps:
                continue
            if CONFIDENCE_RANK[bet.confidence] < CONFIDENCE_RANK[q.min_confidence]:
                continue
            if q.sport_key and bet.sport_key != q.sport_key:
                continue
            if q.market and bet.market != q.market:
                continue
            if q.hide_suspicious and bet.suspicious:
                continue
            offers = [
                (quote, ev) for quote, ev in bet.offers
                if ev * 100 >= q.min_ev_pct and (q.books is None or quote.book in q.books)
            ]
            if offers:
                out.append(ev_payload(bet, offers, q.bankroll, q.kelly, q.round_to, store.first_seen.get(bet.id)))
        if q.sort == "likely":
            out.sort(key=lambda b: b["fair_prob"], reverse=True)
        return out

    return store.memo(("ev", q), compute)


@router.get("/ev")
async def get_ev(q: EvQuery = Depends(ev_query)) -> Response:
    return Response(
        orjson.dumps(select_ev(q)),
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/ev/sharp-books")
async def sharp_books() -> dict[str, list[str]]:
    """Reference books in priority order, and the books that only cross-check them."""
    return {"reference_priority": list(REFERENCE_PRIORITY), "cross_checks": list(CROSS_CHECKS)}

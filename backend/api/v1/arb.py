"""
Arb endpoints.

GET  /arb/opportunities — current arbs (and optional near-misses), JSON
GET  /arb/stream        — same payload pushed over SSE whenever odds update
POST /arb/calc          — manual calculator: stakes for any set of prices
GET  /status            — poller/scanner health, credits, timings

Scanning happens once per poll in the store. Requests only filter and size
stakes, and identical requests within one snapshot share serialized bytes.
"""
from dataclasses import dataclass

import orjson
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.arb_engine import ArbCandidate, ScanConfig, scan_games, to_payload
from services.odds_math import (
    american_to_decimal,
    arb_return_pct,
    balanced_stakes,
    guaranteed_profit,
    round_stakes,
)
from services.odds_store import store

router = APIRouter(tags=["arb"])

SSE_KEEPALIVE_SECONDS = 15.0


@dataclass(frozen=True)
class ArbQuery:
    sport_key: str | None
    market: str | None
    min_profit_pct: float
    books: frozenset[str] | None
    bankroll: float
    round_to: float
    include_live: bool
    hide_suspicious: bool


def arb_query(
    sport_key: str | None = Query(None, description="Odds API sport key, e.g. basketball_nba"),
    market: str | None = Query(None, pattern="^(h2h|spreads|totals)$"),
    min_profit_pct: float = Query(0.0, ge=-5, description="Negative values include near-misses"),
    books: str | None = Query(None, description="Comma-separated book keys you can bet at"),
    bankroll: float = Query(100.0, gt=0, le=1_000_000, description="Total stake across all legs"),
    round_to: float = Query(0.0, ge=0, description="Round stakes to this increment, e.g. 1 or 5"),
    include_live: bool = Query(False),
    hide_suspicious: bool = Query(False),
) -> ArbQuery:
    book_set = frozenset(b.strip() for b in books.split(",") if b.strip()) if books else None
    return ArbQuery(sport_key, market, min_profit_pct, book_set or None, bankroll, round_to, include_live, hide_suspicious)


def _candidates(q: ArbQuery) -> list[ArbCandidate]:
    """The default scan is precomputed; book filters or live mode need their own scan (memoized)."""
    if q.books is None and q.include_live == store.default_scan_config().include_live:
        return store.arbs
    base = store.default_scan_config()
    cfg = ScanConfig(
        max_quote_age_s=base.max_quote_age_s,
        include_live=q.include_live,
        books=q.books,
        min_return_pct=base.min_return_pct,
    )
    return store.memo(("scan", q.books, q.include_live), lambda: scan_games(store.games, cfg))


def select_arbs(q: ArbQuery) -> list[dict]:
    def compute() -> list[dict]:
        out = []
        for c in _candidates(q):
            if c.return_pct < q.min_profit_pct:
                break  # sorted best-first
            if q.sport_key and c.sport_key != q.sport_key:
                continue
            if q.market and c.market != q.market:
                continue
            if q.hide_suspicious and c.suspicious:
                continue
            out.append(to_payload(c, q.bankroll, q.round_to, store.first_seen.get(c.id)))
        return out

    return store.memo(("arbs", q), compute)


def _envelope(q: ArbQuery) -> bytes:
    return store.memo(
        ("arbs-bytes", q),
        lambda: orjson.dumps({"version": store.version, "polled_at": store.polled_at, "arbs": select_arbs(q)}),
    )


@router.get("/arb/opportunities")
async def get_arb_opportunities(q: ArbQuery = Depends(arb_query)) -> Response:
    """Plain list for backwards compatibility with the Next.js client."""
    body = store.memo(("arbs-list-bytes", q), lambda: orjson.dumps(select_arbs(q)))
    return Response(body, media_type="application/json", headers={"Cache-Control": "no-store"})


@router.get("/arb/stream")
async def stream_arbs(request: Request, q: ArbQuery = Depends(arb_query)) -> StreamingResponse:
    """
    Server-Sent Events: sends the current arbs immediately, then again on every
    odds update. Clients get new arbs the instant a poll lands instead of
    waiting for their next refresh tick.
    """
    async def events():
        sent_version = -1
        while not await request.is_disconnected():
            if store.version != sent_version:
                sent_version = store.version
                yield b"event: arbs\ndata: " + _envelope(q) + b"\n\n"
            elif not await store.changed(SSE_KEEPALIVE_SECONDS):
                yield b": keepalive\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


class CalcRequest(BaseModel):
    odds: list[float] = Field(min_length=2, max_length=10, description="American odds, one per outcome")
    bankroll: float = Field(100.0, gt=0)
    round_to: float = Field(0.0, ge=0)


@router.post("/arb/calc")
async def calc_arb(body: CalcRequest) -> dict:
    if any(-100 < o < 100 for o in body.odds):
        raise HTTPException(422, detail="American odds must be <= -100 or >= +100")
    decimals = [american_to_decimal(o) for o in body.odds]
    stakes = round_stakes(balanced_stakes(decimals, body.bankroll), body.round_to)
    return {
        "is_arb": arb_return_pct(decimals) > 0,
        "profit_pct": round(arb_return_pct(decimals), 3),
        "total_stake": round(sum(stakes), 2),
        "guaranteed_profit": round(guaranteed_profit(stakes, decimals), 2),
        "legs": [
            {"odds": o, "stake": round(s, 2), "payout": round(s * d, 2)}
            for o, s, d in zip(body.odds, stakes, decimals)
        ],
    }


@router.get("/status")
async def status() -> dict:
    return store.status()

"""
Server-rendered pages: Arbs (/) and +EV (/ev).

All rendering is Python (Jinja2). The page's JavaScript only opens an
EventSource and swaps in the HTML fragment the server pushes on every odds
update — no build step, no client-side state beyond the user's settings.
"""
import dataclasses
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from api.v1.arb import SSE_KEEPALIVE_SECONDS, ArbQuery, arb_query, select_arbs
from api.v1.ev import EvQuery, ev_query, select_ev
from services.ev_engine import SHARP_WEIGHTS
from services.odds_store import store

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

MARKET_NAMES = {"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"}
SHARP_NAMES = "Pinnacle, BetOnline, Novig and ProphetX"


def available_books(exclude_sharp: bool = False) -> list[tuple[str, str]]:
    def compute() -> list[tuple[str, str]]:
        books: dict[str, str] = {}
        for game in store.games:
            for b in game.get("bookmakers", ()):
                if exclude_sharp and b["key"] in SHARP_WEIGHTS:
                    continue
                books.setdefault(b["key"], b.get("title", b["key"]))
        return sorted(books.items(), key=lambda kv: kv[1].lower())

    return store.memo(("books", exclude_sharp), compute)


def render_arbs(q: ArbQuery) -> str:
    def compute() -> str:
        arbs = select_arbs(q)
        return templates.get_template("_board.html").render(
            arbs=[a for a in arbs if a["profit_pct"] > 0],
            near=[a for a in arbs if a["profit_pct"] <= 0],
            status=store.status(),
            market_names=MARKET_NAMES,
        )

    return store.memo(("board", q), compute)


def render_ev(q: EvQuery) -> str:
    return store.memo(("ev-board", q), lambda: templates.get_template("_ev_board.html").render(
        bets=select_ev(q),
        status=store.status(),
        market_names=MARKET_NAMES,
    ))


def _sse(request: Request, render: Callable[[], str]) -> StreamingResponse:
    """Push freshly rendered HTML on every store update; keepalive comments otherwise."""
    async def events():
        sent_version = -1
        while not await request.is_disconnected():
            if store.version != sent_version:
                sent_version = store.version
                payload = "".join(f"data: {line}\n" for line in render().splitlines())
                yield f"event: board\n{payload}\n".encode()
            elif not await store.changed(SSE_KEEPALIVE_SECONDS):
                yield b": keepalive\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.get("/", response_class=HTMLResponse)
async def arbs_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "arbs.html", {
        "page": "arbs", "stream": "/ui/stream", "books": available_books(),
        "alert_text": "A new guaranteed-profit line is open.",
    })


@router.get("/ev", response_class=HTMLResponse)
async def ev_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "ev.html", {
        "page": "ev", "stream": "/ui/ev/stream", "books": available_books(exclude_sharp=True),
        "sharp_names": SHARP_NAMES, "alert_text": "A new +EV bet beat the sharp line.",
    })


@router.get("/ui/stream")
async def arbs_stream(
    request: Request,
    q: ArbQuery = Depends(arb_query),
    near: bool = Query(False),
) -> StreamingResponse:
    if near:
        q = dataclasses.replace(q, min_profit_pct=-1.0)
    return _sse(request, lambda: render_arbs(q))


@router.get("/ui/ev/stream")
async def ev_stream(
    request: Request,
    q: EvQuery = Depends(ev_query),
    min_prob_pct: float = Query(0.0, ge=0, le=100),
) -> StreamingResponse:
    q = dataclasses.replace(q, min_prob=min_prob_pct / 100)
    return _sse(request, lambda: render_ev(q))

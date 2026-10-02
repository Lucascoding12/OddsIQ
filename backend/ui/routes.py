"""
Server-rendered arb screen.

All rendering is Python (Jinja2). The page's JavaScript only opens an
EventSource and swaps in the HTML fragment the server pushes on every odds
update — no build step, no client-side state beyond the user's settings.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from api.v1.arb import SSE_KEEPALIVE_SECONDS, ArbQuery, arb_query, select_arbs
from services.odds_store import store

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

MARKET_NAMES = {"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"}


def available_books() -> list[tuple[str, str]]:
    def compute() -> list[tuple[str, str]]:
        books: dict[str, str] = {}
        for game in store.games:
            for b in game.get("bookmakers", ()):
                books.setdefault(b["key"], b.get("title", b["key"]))
        return sorted(books.items(), key=lambda kv: kv[1].lower())

    return store.memo("books", compute)


def render_board(q: ArbQuery) -> str:
    def compute() -> str:
        arbs = select_arbs(q)
        return templates.get_template("_board.html").render(
            arbs=[a for a in arbs if a["profit_pct"] > 0],
            near=[a for a in arbs if a["profit_pct"] <= 0],
            status=store.status(),
            market_names=MARKET_NAMES,
        )

    return store.memo(("board", q), compute)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"books": available_books()})


@router.get("/ui/stream")
async def ui_stream(request: Request, q: ArbQuery = Depends(arb_query)) -> StreamingResponse:
    """SSE of rendered board HTML. Each line is prefixed with `data:` per the SSE spec."""
    async def events():
        sent_version = -1
        while not await request.is_disconnected():
            if store.version != sent_version:
                sent_version = store.version
                html = render_board(q)
                payload = "".join(f"data: {line}\n" for line in html.splitlines())
                yield f"event: board\n{payload}\n".encode()
            elif not await store.changed(SSE_KEEPALIVE_SECONDS):
                yield b": keepalive\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )

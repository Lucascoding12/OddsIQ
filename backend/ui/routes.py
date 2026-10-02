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
from starlette.exceptions import HTTPException
from fastapi.templating import Jinja2Templates

from api.v1.arb import SSE_KEEPALIVE_SECONDS, ArbQuery, arb_query, select_arbs
from api.v1.ev import EvQuery, ev_query, select_ev
from api.v1.tools import sharp_summary
from services import calculators, kelly, line_shop
from services.markets import label
from services.odds_math import american_to_decimal, kelly_fraction
from services.ev_engine import SHARP_BOOKS
from services.odds_store import store

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

MARKET_NAMES = {"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"}
SHARP_NAMES = "Pinnacle (then Betfair, Kalshi, Polymarket), checked against BetOnline, Novig and ProphetX"


def available_books(exclude_sharp: bool = False) -> list[tuple[str, str]]:
    def compute() -> list[tuple[str, str]]:
        books: dict[str, str] = {}
        for game in store.games:
            for b in game.get("bookmakers", ()):
                if exclude_sharp and b["key"] in SHARP_BOOKS:
                    continue
                books.setdefault(b["key"], b.get("title", b["key"]))
        return sorted(books.items(), key=lambda kv: kv[1].lower())

    return store.memo(("books", exclude_sharp), compute)


def render_arbs(q: ArbQuery) -> str:
    def compute() -> str:
        arbs = select_arbs(q)
        return templates.get_template("_board.html").render(
            arbs=[a for a in arbs if a["is_arb"]],
            near=[a for a in arbs if not a["is_arb"]],
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


def available_sports() -> list[tuple[str, str]]:
    return store.memo("sports", lambda: sorted(
        {(g.get("sport_key", ""), g.get("sport_title", g.get("sport_key", ""))) for g in store.games},
        key=lambda kv: kv[1],
    ))


@router.get("/sharp", response_class=HTMLResponse)
async def sharp_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sharp.html", {
        "page": "sharp", "stream": "/ui/sharp/stream", "sports": available_sports(),
        "sharp_names": SHARP_NAMES, "books": [],
    })


@router.get("/ui/sharp/stream")
async def sharp_stream(request: Request, sport_key: str | None = Query(None)) -> StreamingResponse:
    sport_key = sport_key or None
    return _sse(request, lambda: store.memo(("sharp-board", sport_key), lambda: templates.get_template("_sharp_board.html").render(
        status=store.status(), **sharp_summary(sport_key),
    )))


@router.get("/shop", response_class=HTMLResponse)
async def shop_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "shop.html", {
        "page": "shop", "stream": "/ui/shop/stream", "books": [],
        "teams": store.memo("teams", lambda: line_shop.suggestions(store.grouped)),
    })


@router.get("/ui/shop/stream")
async def shop_stream(request: Request, q: str = Query("", max_length=100)) -> StreamingResponse:
    query = q.strip()
    return _sse(request, lambda: store.memo(("shop-board", query), lambda: templates.get_template("_shop_board.html").render(
        status=store.status(), query=query, games=line_shop.search(store.grouped, query),
    )))


@router.get("/calc", response_class=HTMLResponse)
async def calc_page(request: Request, c: str = Query("arbitrage")) -> HTMLResponse:
    calc = calculators.BY_SLUG.get(c, calculators.BY_SLUG["arbitrage"])
    result, error = calculators.run(calc, {})
    return templates.TemplateResponse(request, "calc.html", {
        "page": "calc", "stream": "", "books": [],
        "calculators": calculators.CALCULATORS, "calc": calc,
        "result_html": templates.get_template("_calc_result.html").render(result=result, error=error),
    })


@router.get("/ui/calc/{slug}", response_class=HTMLResponse)
async def calc_result(request: Request, slug: str) -> HTMLResponse:
    calc = calculators.BY_SLUG.get(slug)
    if calc is None:
        raise HTTPException(404)
    result, error = calculators.run(calc, dict(request.query_params))
    return HTMLResponse(templates.get_template("_calc_result.html").render(result=result, error=error))


def _live_bet_options() -> list[dict]:
    """Current +EV bets with fair or strong confidence, for the Kelly page's picker."""
    def compute() -> list[dict]:
        out = []
        for b in store.ev_bets:
            if b.confidence == "thin":
                continue
            q, ev = b.offers[0]
            out.append({
                "id": b.id,
                "label": f"{label(b.market, b.selection, b.point)} {q.american:+d} at {q.book_title}",
                "game": f"{b.away_team} at {b.home_team}",
                "book_title": q.book_title, "odds": q.american, "decimal": q.decimal,
                "fair_prob": b.fair_prob, "fair_prob_low": b.fair_prob_low,
                "ev_pct": ev * 100, "confidence": b.confidence, "reference": b.sharp_books[0],
            })
        return out

    return store.memo("kelly-bets", compute)


def _curve_view(p: float, decimal: float, full: float, width: int = 640, height: int = 240) -> dict | None:
    points = kelly.growth_curve(p, decimal)
    if not points:
        return None
    pad_l, pad_r, pad_t, pad_b = 52, 16, 16, 34
    xs = [f for f, _ in points]
    ys = [g for _, g in points]
    y_lo, y_hi = min(min(ys), 0.0), max(ys) * 1.15 or 1.0
    x_hi = xs[-1]

    def sx(f: float) -> float:
        return pad_l + (width - pad_l - pad_r) * f / x_hi

    def sy(g: float) -> float:
        return pad_t + (height - pad_t - pad_b) * (y_hi - g) / (y_hi - y_lo)

    markers = []
    for name, multiple in kelly.FRACTIONS[:3]:
        f = full * multiple
        g = kelly.growth_rate(f, p, decimal) * 100
        markers.append({"name": name, "x": sx(f), "y": sy(g)})
    x_ticks = [{"x": sx(x_hi * i / 4), "label": f"{x_hi * i / 4 * 100:.0f}%"} for i in range(5)]
    y_ticks = [{"y": sy(v), "label": f"{v:.2f}%"} for v in (y_lo, 0.0, max(ys)) if y_lo < 0 or v >= 0]
    return {
        "width": width, "height": height,
        "path": "M" + " L".join(f"{sx(f):.1f},{sy(g):.1f}" for f, g in points),
        "zero_y": sy(0.0), "left": pad_l, "right": width - pad_r, "bottom": height - pad_b,
        "markers": markers, "x_ticks": x_ticks, "y_ticks": y_ticks,
        "points": [[round(f * 100, 2), round(g, 4), round(sx(f), 1), round(sy(g), 1)] for f, g in points],
    }


@router.get("/kelly", response_class=HTMLResponse)
async def kelly_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "kelly.html", {
        "page": "kelly", "stream": "/ui/kelly/stream", "books": [], "live_bets": _live_bet_options(),
    })


@router.get("/ui/kelly/stream")
async def kelly_stream(
    request: Request,
    bankroll: float = Query(1000, gt=0, le=10_000_000),
    odds: str = Query("+110", max_length=12),
    win_pct: float = Query(55, gt=0, lt=100),
    bet: str = Query("", max_length=200),
    multiple: float = Query(0.25, gt=0, le=1),
    max_exposure_pct: float = Query(25, gt=0, le=100),
    round_to: float = Query(1, ge=0),
    conservative: bool = Query(False),
) -> StreamingResponse:
    def render() -> str:
        key = ("kelly-board", bankroll, odds, win_pct, bet, multiple, max_exposure_pct, round_to, conservative)
        return store.memo(key, lambda: _render_kelly(bankroll, odds, win_pct, bet, multiple,
                                                     max_exposure_pct, round_to, conservative))

    return _sse(request, render)


def _render_kelly(bankroll: float, odds: str, win_pct: float, bet_id: str, multiple: float,
                  max_exposure_pct: float, round_to: float, conservative: bool) -> str:
    live = _live_bet_options()
    picked = next((b for b in live if b["id"] == bet_id), None) if bet_id else None
    error = None
    if picked:
        p = picked["fair_prob_low"] if conservative else picked["fair_prob"]
        decimal, american = picked["decimal"], picked["odds"]
    else:
        p = win_pct / 100
        try:
            american = float(odds.replace("+", ""))
            if -100 < american < 100:
                raise ValueError
            decimal = american_to_decimal(american)
        except ValueError:
            error = "Odds must be American odds: −100 or lower, or +100 or higher."
            decimal, american = 2.0, 100.0
    full = kelly_fraction(p, decimal)
    rows = kelly.sizing_table(p, decimal, bankroll, round_to)
    sheet, scale = kelly.kelly_sheet(live, bankroll, multiple, max_exposure_pct / 100, round_to, conservative)
    return templates.get_template("_kelly_board.html").render(
        status=store.status(), error=error, picked=picked, bet_missing=bool(bet_id and not picked),
        p=p, decimal=decimal, american=american, full=full, edge=p * decimal - 1,
        rows=rows, chosen=multiple, curve=_curve_view(p, decimal, full),
        sheet=sheet, scale=scale, bankroll=bankroll, max_exposure_pct=max_exposure_pct,
        sheet_total=sum(r.stake for r in sheet), conservative=conservative,
    )

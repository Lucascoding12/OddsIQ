"""
Arbitrage engine — finds guaranteed-profit combinations across books.

How a game is scanned:
  1. Every bookmaker quote is bucketed into a *group*: a complete set of
     mutually exclusive outcomes that exactly one of will win.
       h2h      → all outcome names the book lists (2-way, or 3-way with Draw)
       spreads  → home at line p  +  away at line -p
       totals   → Over x  +  Under x
     Lines must match exactly across books; mixing lines is a middle, not an arb.
  2. Within each group, keep the best (highest effective decimal) price per outcome.
  3. If every outcome is covered, the group is an arb when sum(1/decimal) < 1.

Quotes are dropped before grouping when they are stale (book's market
last_update too old), the game has started (in-play feeds lag badly, so those
"arbs" are almost always phantoms), or the book is filtered out.

Everything here is pure and synchronous: scanning is CPU work over an
in-memory snapshot, so it runs in milliseconds and needs no I/O.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache

from services.odds_math import (
    american_to_decimal,
    apply_commission,
    arb_return_pct,
    balanced_stakes,
    guaranteed_profit,
    round_stakes,
)

SUPPORTED_MARKETS = ("h2h", "spreads", "totals")

# Exchanges take commission on net winnings. Sportsbooks don't, so they're absent.
# Conservative (highest standard) rates — a real arb must survive the fee.
EXCHANGE_COMMISSION: dict[str, float] = {
    "betfair_ex_uk": 0.05,
    "betfair_ex_eu": 0.05,
    "betfair_ex_au": 0.05,
    "matchbook": 0.02,
    "smarkets": 0.02,
    "betopenly": 0.02,
    "novig": 0.0,
    "prophetx": 0.01,
}

# Returns this high are nearly always a stale line or a palpable error that
# the book will void. Shown, but flagged so nobody fires blind.
SUSPICIOUS_RETURN_PCT = 8.0


@dataclass(slots=True, frozen=True)
class Quote:
    book: str
    book_title: str
    selection: str
    point: float | None
    american: int
    decimal: float  # effective, after any exchange commission
    last_update: str


@dataclass(slots=True)
class ArbCandidate:
    id: str
    game_id: str
    sport_key: str
    sport_title: str
    home_team: str
    away_team: str
    commence_time: str
    market: str
    line: float | None
    legs: tuple[Quote, ...]
    return_pct: float
    book_count: int
    suspicious: bool


@dataclass(slots=True, frozen=True)
class ScanConfig:
    max_quote_age_s: float | None = None
    include_live: bool = False
    books: frozenset[str] | None = None
    min_return_pct: float = 0.0
    commissions: dict[str, float] = field(default_factory=lambda: EXCHANGE_COMMISSION)


@lru_cache(maxsize=8192)
def _parse_ts(ts: str) -> float:
    """ISO-8601 → epoch seconds. Cached because thousands of quotes share timestamps."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def _label(market: str, selection: str, point: float | None) -> str:
    if market == "h2h" or point is None:
        return selection
    if market == "spreads":
        return f"{selection} {point:+g}"
    return f"{selection} {point:g}"


def scan_game(game: dict, now: float, cfg: ScanConfig) -> list[ArbCandidate]:
    commence = game.get("commence_time") or ""
    if not cfg.include_live and commence and _parse_ts(commence) <= now:
        return []

    home = game.get("home_team", "")
    away = game.get("away_team", "")

    # group key → selection → best quote
    best: dict[tuple, dict[str, Quote]] = {}
    # group key → books quoting it (a 1-book "arb" is a pricing error, not an arb)
    group_books: dict[tuple, set[str]] = {}
    required: dict[tuple, frozenset[str]] = {}

    for book in game.get("bookmakers", ()):
        book_key = book.get("key", "")
        if cfg.books is not None and book_key not in cfg.books:
            continue
        commission = cfg.commissions.get(book_key, 0.0)
        book_title = book.get("title", book_key)

        for market in book.get("markets", ()):
            mkey = market.get("key")
            if mkey not in SUPPORTED_MARKETS:
                continue
            updated = market.get("last_update") or book.get("last_update") or ""
            if cfg.max_quote_age_s is not None and updated and now - _parse_ts(updated) > cfg.max_quote_age_s:
                continue

            outcomes = market.get("outcomes", ())
            if mkey == "h2h":
                names = frozenset(o["name"] for o in outcomes)
                if len(names) < 2:
                    continue
                gkey: tuple = ("h2h", None, names)
                required[gkey] = names

            for o in outcomes:
                name = o["name"]
                point = o.get("point")
                if mkey == "spreads":
                    if point is None or name not in (home, away):
                        continue
                    home_line = point if name == home else -point
                    gkey = ("spreads", home_line)
                    required.setdefault(gkey, frozenset((home, away)))
                elif mkey == "totals":
                    if point is None:
                        continue
                    gkey = ("totals", point)
                    required.setdefault(gkey, frozenset(("Over", "Under")))

                american = o["price"]
                decimal = american_to_decimal(american)
                if commission:
                    decimal = apply_commission(decimal, commission)

                sel = best.setdefault(gkey, {})
                current = sel.get(name)
                if current is None or decimal > current.decimal:
                    sel[name] = Quote(book_key, book_title, name, point, american, decimal, updated)
                group_books.setdefault(gkey, set()).add(book_key)

    results: list[ArbCandidate] = []
    for gkey, sel in best.items():
        needed = required[gkey]
        if len(sel) != len(needed) or not needed.issubset(sel):
            continue
        legs = tuple(sorted(sel.values(), key=lambda q: q.selection))
        ret = arb_return_pct([q.decimal for q in legs])
        if ret < cfg.min_return_pct:
            continue

        market = gkey[0]
        line = gkey[1]
        leg_books = {q.book for q in legs}
        results.append(ArbCandidate(
            id=f"{game.get('id')}:{market}:{'' if line is None else f'{line:g}'}:{'|'.join(q.book for q in legs)}",
            game_id=game.get("id", ""),
            sport_key=game.get("sport_key", ""),
            sport_title=game.get("sport_title", game.get("sport_key", "")),
            home_team=home,
            away_team=away,
            commence_time=commence,
            market=market,
            line=line,
            legs=legs,
            return_pct=ret,
            book_count=len(group_books[gkey]),
            suspicious=ret > SUSPICIOUS_RETURN_PCT or len(leg_books) == 1,
        ))
    return results


def scan_games(games: list[dict], cfg: ScanConfig, now: float | None = None) -> list[ArbCandidate]:
    """Scan every game, best return first."""
    if now is None:
        now = datetime.now(timezone.utc).timestamp()
    results: list[ArbCandidate] = []
    for game in games:
        results.extend(scan_game(game, now, cfg))
    results.sort(key=lambda c: c.return_pct, reverse=True)
    return results


def to_payload(
    c: ArbCandidate,
    bankroll: float = 100.0,
    round_to: float = 0.0,
    first_seen: str | None = None,
) -> dict:
    """
    JSON shape for the API. Stakes are computed per request because they depend
    on the caller's bankroll; the scan itself is shared.
    Keeps the original field names (profit_pct, total_stake, legs[].odds ...)
    so older clients keep working.
    """
    decimals = [q.decimal for q in c.legs]
    stakes = round_stakes(balanced_stakes(decimals, bankroll), round_to)
    profit = guaranteed_profit(stakes, decimals)
    total = sum(stakes)
    return {
        "id": c.id,
        "game_id": c.game_id,
        "sport_key": c.sport_key,
        "sport_title": c.sport_title,
        "home_team": c.home_team,
        "away_team": c.away_team,
        "commence_time": c.commence_time,
        "market": c.market,
        "line": c.line,
        "profit_pct": round(c.return_pct, 3),
        "total_stake": round(total, 2),
        "guaranteed_profit": round(profit, 2),
        "book_count": c.book_count,
        "suspicious": c.suspicious,
        "first_seen": first_seen,
        "legs": [
            {
                "book": q.book,
                "book_title": q.book_title,
                "outcome": _label(c.market, q.selection, q.point),
                "odds": q.american,
                "decimal": round(q.decimal, 4),
                "stake": round(s, 2),
                "payout": round(s * q.decimal, 2),
                "last_update": q.last_update,
            }
            for q, s in zip(c.legs, stakes)
        ],
    }

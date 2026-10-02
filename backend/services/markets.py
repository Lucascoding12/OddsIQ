"""
Market grouping shared by the arb and +EV engines.

A *group* is a complete set of mutually exclusive outcomes, exactly one of
which wins:
  h2h      → all outcome names the book lists (2-way, or 3-way with Draw)
  spreads  → home at line p  +  away at line -p
  totals   → Over x  +  Under x
Lines must match exactly across books; mixing lines is a middle, not an arb,
and comparing different lines would make an EV estimate meaningless.

Quotes are dropped before grouping when stale, when the game has started
(in-play feeds lag badly), or when the book is filtered out.
"""
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache

from services.odds_math import american_to_decimal, apply_commission

SUPPORTED_MARKETS = ("h2h", "spreads", "totals")

# Exchanges take commission on net winnings. Sportsbooks don't, so they're absent.
# Conservative (highest standard) rates — an edge must survive the fee.
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

# Group key: ("h2h", None, frozenset(names)) | ("spreads", home_line) | ("totals", line)
GroupKey = tuple


@dataclass(slots=True, frozen=True)
class Quote:
    book: str
    book_title: str
    selection: str
    point: float | None
    american: int
    decimal: float  # effective, after any exchange commission
    last_update: str


@dataclass(slots=True, frozen=True)
class ScanConfig:
    max_quote_age_s: float | None = None
    include_live: bool = False
    books: frozenset[str] | None = None
    min_return_pct: float = 0.0
    commissions: dict[str, float] = field(default_factory=lambda: EXCHANGE_COMMISSION)


@dataclass(slots=True)
class GameMarkets:
    game: dict
    # group → book → selection → quote
    groups: dict[GroupKey, dict[str, dict[str, Quote]]]
    required: dict[GroupKey, frozenset[str]]

    def complete_books(self, gkey: GroupKey) -> dict[str, dict[str, Quote]]:
        """Books quoting every outcome in the group (needed to de-vig a single book)."""
        needed = self.required[gkey]
        return {b: sel for b, sel in self.groups[gkey].items() if needed.issubset(sel)}


@lru_cache(maxsize=8192)
def parse_ts(ts: str) -> float:
    """ISO-8601 → epoch seconds. Cached because thousands of quotes share timestamps."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def label(market: str, selection: str, point: float | None) -> str:
    if market == "h2h" or point is None:
        return selection
    if market == "spreads":
        return f"{selection} {point:+g}"
    return f"{selection} {point:g}"


def group_game(game: dict, now: float, cfg: ScanConfig) -> GameMarkets | None:
    commence = game.get("commence_time") or ""
    if not cfg.include_live and commence and parse_ts(commence) <= now:
        return None

    home = game.get("home_team", "")
    away = game.get("away_team", "")
    groups: dict[GroupKey, dict[str, dict[str, Quote]]] = {}
    required: dict[GroupKey, frozenset[str]] = {}

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
            if cfg.max_quote_age_s is not None and updated and now - parse_ts(updated) > cfg.max_quote_age_s:
                continue

            outcomes = market.get("outcomes", ())
            if mkey == "h2h":
                names = frozenset(o["name"] for o in outcomes)
                if len(names) < 2:
                    continue
                gkey: GroupKey = ("h2h", None, names)
                required[gkey] = names

            for o in outcomes:
                name = o["name"]
                point = o.get("point")
                if mkey == "spreads":
                    if point is None or name not in (home, away):
                        continue
                    gkey = ("spreads", point if name == home else -point)
                    required.setdefault(gkey, frozenset((home, away)))
                elif mkey == "totals":
                    if point is None:
                        continue
                    gkey = ("totals", point)
                    required.setdefault(gkey, frozenset(("Over", "Under")))

                decimal = american_to_decimal(o["price"])
                if commission:
                    decimal = apply_commission(decimal, commission)
                groups.setdefault(gkey, {}).setdefault(book_key, {})[name] = Quote(
                    book_key, book_title, name, point, o["price"], decimal, updated,
                )

    return GameMarkets(game, groups, required)

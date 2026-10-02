"""
Sharp metrics — signals derived from how sharp and soft books price the same market.

  sharp_vs_public  Where the sharp fair line disagrees with the soft-book
                   consensus. Soft books shade toward public money, so the
                   side sharps rate higher is the "sharp side".
  line_moves       Price changes since the tracker first saw each quote.
                   Steam = two or more sharp books moving the same way;
                   soft books that haven't followed yet are the opportunity.
  disagreement     Biggest best-vs-worst gaps across books on one outcome.
  book_holds       Average margin per book across live markets. Low hold
                   is the clearest live sign of a sharp book.

All functions are pure over the grouped snapshot; only MoveTracker keeps state.
"""
import statistics
from dataclasses import dataclass

from services.ev_engine import SHARP_WEIGHTS, fair_line
from services.markets import GameMarkets, label
from services.odds_math import devig_power

MARKET_NAMES = {"h2h": "moneyline", "spreads": "spread", "totals": "total"}
# Probability moves smaller than this are price ticks, not information.
MOVE_THRESHOLD = 0.015
STEAM_MIN_SHARP_BOOKS = 2


def _game_label(game: dict) -> str:
    return f"{game.get('away_team', '')} at {game.get('home_team', '')}"


def _base(gm: GameMarkets, gkey: tuple) -> dict:
    game = gm.game
    return {
        "game": _game_label(game),
        "sport_title": game.get("sport_title", game.get("sport_key", "")),
        "commence_time": game.get("commence_time", ""),
        "market": MARKET_NAMES.get(gkey[0], gkey[0]),
    }


def _point(gm: GameMarkets, gkey: tuple, selection: str) -> float | None:
    for quotes in gm.groups[gkey].values():
        if selection in quotes:
            return quotes[selection].point
    return None


def sharp_vs_public(grouped: list[GameMarkets], min_soft_books: int = 3) -> list[dict]:
    rows = []
    for gm in grouped:
        for gkey in gm.groups:
            fair = fair_line(gm, gkey)
            if fair is None:
                continue
            sharp_probs, sharp_titles = fair
            selections = sorted(gm.required[gkey])
            soft = [
                devig_power([quotes[s].decimal for s in selections])
                for book, quotes in gm.complete_books(gkey).items()
                if book not in SHARP_WEIGHTS
            ]
            if len(soft) < min_soft_books:
                continue
            public = [statistics.fmean(p[i] for p in soft) for i in range(len(selections))]
            gaps = [(sharp_probs[s] - public[i], s, i) for i, s in enumerate(selections)]
            gap, sel, i = max(gaps)
            rows.append({
                **_base(gm, gkey),
                "pick": label(gkey[0], sel, _point(gm, gkey, sel)),
                "sharp_prob": sharp_probs[sel],
                "public_prob": public[i],
                "gap_pts": gap * 100,
                "sharp_books": list(sharp_titles),
                "soft_books": len(soft),
            })
    rows.sort(key=lambda r: r["gap_pts"], reverse=True)
    return rows


def disagreement(grouped: list[GameMarkets], min_gap: float = 0.02) -> list[dict]:
    rows = []
    for gm in grouped:
        for gkey, by_book in gm.groups.items():
            for sel in gm.required[gkey]:
                quotes = [q[sel] for q in by_book.values() if sel in q]
                if len(quotes) < 3:
                    continue
                best = max(quotes, key=lambda q: q.decimal)
                worst = min(quotes, key=lambda q: q.decimal)
                gap = 1 / worst.decimal - 1 / best.decimal
                if gap < min_gap:
                    continue
                rows.append({
                    **_base(gm, gkey),
                    "pick": label(gkey[0], sel, best.point),
                    "best": {"book_title": best.book_title, "odds": best.american},
                    "worst": {"book_title": worst.book_title, "odds": worst.american},
                    "gap_pts": gap * 100,
                    "book_count": len(quotes),
                })
    rows.sort(key=lambda r: r["gap_pts"], reverse=True)
    return rows


def book_holds(grouped: list[GameMarkets]) -> list[dict]:
    holds: dict[str, list[float]] = {}
    titles: dict[str, str] = {}
    for gm in grouped:
        for gkey in gm.groups:
            selections = gm.required[gkey]
            for book, quotes in gm.complete_books(gkey).items():
                holds.setdefault(book, []).append(sum(1 / quotes[s].decimal for s in selections) - 1)
                titles[book] = next(iter(quotes.values())).book_title
    rows = [
        {"book": b, "book_title": titles[b], "avg_hold_pct": statistics.fmean(h) * 100,
         "markets": len(h), "sharp": b in SHARP_WEIGHTS}
        for b, h in holds.items() if len(h) >= 5
    ]
    rows.sort(key=lambda r: r["avg_hold_pct"])
    return rows


@dataclass(slots=True)
class Seen:
    american: int
    decimal: float
    at: str


class MoveTracker:
    """
    Remembers the first price seen for every (game, line, outcome, book) while
    the process runs, so moves can be measured against it. Entries for games
    that leave the feed are dropped.
    """

    def __init__(self) -> None:
        self.opening: dict[tuple, Seen] = {}
        self.since: str | None = None

    def observe(self, grouped: list[GameMarkets], now_iso: str) -> None:
        live: set[tuple] = set()
        for gm in grouped:
            gid = gm.game.get("id")
            for gkey, by_book in gm.groups.items():
                for book, quotes in by_book.items():
                    for sel, q in quotes.items():
                        key = (gid, gkey, sel, book)
                        live.add(key)
                        if key not in self.opening:
                            self.opening[key] = Seen(q.american, q.decimal, now_iso)
        self.opening = {k: v for k, v in self.opening.items() if k in live}
        self.since = self.since or now_iso

    def moves(self, grouped: list[GameMarkets]) -> list[dict]:
        rows = []
        for gm in grouped:
            gid = gm.game.get("id")
            for gkey, by_book in gm.groups.items():
                for sel in gm.required[gkey]:
                    moved = []
                    for book, quotes in by_book.items():
                        q = quotes.get(sel)
                        seen = self.opening.get((gid, gkey, sel, book))
                        if q is None or seen is None:
                            continue
                        # Positive = the outcome got more likely (price shortened).
                        delta = 1 / q.decimal - 1 / seen.decimal
                        moved.append((book, q, seen, delta))
                    sharp = [m for m in moved if m[0] in SHARP_WEIGHTS and abs(m[3]) >= MOVE_THRESHOLD]
                    if not sharp:
                        continue
                    direction = 1 if sum(m[3] for m in sharp) > 0 else -1
                    agreeing = [m for m in sharp if (m[3] > 0) == (direction > 0)]
                    lagging = [
                        m for m in moved
                        if m[0] not in SHARP_WEIGHTS and abs(m[3]) < MOVE_THRESHOLD
                    ]
                    rows.append({
                        **_base(gm, gkey),
                        "pick": label(gkey[0], sel, agreeing[0][1].point),
                        "direction": "toward" if direction > 0 else "away from",
                        "sharp_moves": [
                            {"book_title": q.book_title, "from": seen.american, "to": q.american}
                            for _, q, seen, _ in agreeing
                        ],
                        "move_pts": statistics.fmean(abs(m[3]) for m in agreeing) * 100,
                        "steam": len(agreeing) >= STEAM_MIN_SHARP_BOOKS,
                        "lagging": [
                            {"book_title": q.book_title, "odds": q.american} for _, q, _, _ in lagging
                        ],
                    })
        rows.sort(key=lambda r: (r["steam"], r["move_pts"]), reverse=True)
        return rows

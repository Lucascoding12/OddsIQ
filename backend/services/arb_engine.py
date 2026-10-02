"""
Arbitrage engine — finds guaranteed-profit combinations across books.

Quotes are grouped into complete outcome sets by services.markets. Within each
group we keep the best effective price per outcome; the group is an arb when
sum(1/decimal) < 1.

Everything here is pure and synchronous: scanning is CPU work over an
in-memory snapshot, so it runs in milliseconds and needs no I/O.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

from services.markets import GameMarkets, Quote, ScanConfig, group_game, label
from services.odds_math import arb_return_pct, best_rounded_stakes, guaranteed_profit

# Returns this high are nearly always a stale line or a palpable error that
# the book will void. Shown, but flagged so nobody fires blind.
SUSPICIOUS_RETURN_PCT = 8.0


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


def scan_game(game: dict, now: float, cfg: ScanConfig) -> list[ArbCandidate]:
    gm = group_game(game, now, cfg)
    return [] if gm is None else arbs_from_grouped(gm, cfg)


def arbs_from_grouped(gm: GameMarkets, cfg: ScanConfig) -> list[ArbCandidate]:
    game = gm.game
    results: list[ArbCandidate] = []
    for gkey, by_book in gm.groups.items():
        needed = gm.required[gkey]
        best: dict[str, Quote] = {}
        for quotes in by_book.values():
            for name, q in quotes.items():
                current = best.get(name)
                if current is None or q.decimal > current.decimal:
                    best[name] = q
        if len(best) != len(needed) or not needed.issubset(best):
            continue

        legs = tuple(sorted(best.values(), key=lambda q: q.selection))
        ret = arb_return_pct([q.decimal for q in legs])
        if ret < cfg.min_return_pct:
            continue

        market, line = gkey[0], gkey[1]
        results.append(ArbCandidate(
            id=f"{game.get('id')}:{market}:{'' if line is None else f'{line:g}'}:{'|'.join(q.book for q in legs)}",
            game_id=game.get("id", ""),
            sport_key=game.get("sport_key", ""),
            sport_title=game.get("sport_title", game.get("sport_key", "")),
            home_team=game.get("home_team", ""),
            away_team=game.get("away_team", ""),
            commence_time=game.get("commence_time") or "",
            market=market,
            line=line,
            legs=legs,
            return_pct=ret,
            book_count=len(by_book),
            suspicious=ret > SUSPICIOUS_RETURN_PCT or len({q.book for q in legs}) == 1,
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
    stakes = best_rounded_stakes(decimals, bankroll, round_to)
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
                "outcome": label(c.market, q.selection, q.point),
                "odds": q.american,
                "decimal": round(q.decimal, 4),
                "stake": round(s, 2),
                "payout": round(s * q.decimal, 2),
                "last_update": q.last_update,
            }
            for q, s in zip(c.legs, stakes)
        ],
    }

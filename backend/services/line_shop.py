"""
Line shopping — find the best book for a bet you already have in mind.

Queries read like bets: "chiefs -3.5", "over 47.5 bills", "yankees ml".
  - words match team or league names (every word must match the game)
  - ml / moneyline, spread / ats, over / under / total pick the market
  - numbers pick the line (sign ignored, so "chiefs 3.5" also finds -3.5)
  - a team name or over/under picks which side to put first

Every book quoting the line is ranked best to worst, with the edge against
the sharp fair price when sharp books quote it too.
"""
import re
from dataclasses import dataclass

from services.ev_engine import SHARP_BOOKS, fair_line
from services.markets import GameMarkets, label
from services.odds_math import american_to_decimal, expected_value

MARKET_WORDS = {
    "ml": "h2h", "moneyline": "h2h", "h2h": "h2h",
    "spread": "spreads", "spreads": "spreads", "ats": "spreads",
    "total": "totals", "totals": "totals", "over": "totals", "under": "totals",
}
MARKET_NAMES = {"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"}
LINES_PER_MARKET = 2
MAX_GAMES = 10


@dataclass(frozen=True)
class ParsedQuery:
    words: tuple[str, ...]
    market: str | None
    points: tuple[float, ...]
    side_word: str | None  # "over" / "under"


def parse(query: str) -> ParsedQuery:
    words, points = [], []
    market = side = None
    for token in query.lower().split():
        number = re.fullmatch(r"[ou]?([+-]?\d+(?:\.\d+)?)", token)
        if number and not token.isalpha():
            points.append(abs(float(number.group(1))))
            if token[0] in "ou":
                market, side = "totals", "over" if token[0] == "o" else "under"
            continue
        if token in MARKET_WORDS:
            market = MARKET_WORDS[token]
            if token in ("over", "under"):
                side = token
            continue
        words.append(token)
    return ParsedQuery(tuple(words), market, tuple(points), side)


def _matches(game: dict, words: tuple[str, ...]) -> bool:
    haystack = " ".join((game.get("home_team", ""), game.get("away_team", ""), game.get("sport_title", ""))).lower()
    return all(w in haystack for w in words)


def _focus(game: dict, pq: ParsedQuery) -> str | None:
    if pq.side_word:
        return pq.side_word.title()
    for team in (game.get("home_team", ""), game.get("away_team", "")):
        if any(w in team.lower() for w in pq.words):
            return team
    return None


def search(grouped: list[GameMarkets], query: str) -> list[dict]:
    pq = parse(query)
    if not pq.words and not pq.points:
        return []
    results = []
    for gm in grouped:
        if not _matches(gm.game, pq.words):
            continue
        focus = _focus(gm.game, pq)
        blocks = _blocks(gm, pq, focus)
        if blocks:
            results.append({
                "game": f"{gm.game.get('away_team')} at {gm.game.get('home_team')}",
                "sport_title": gm.game.get("sport_title", ""),
                "commence_time": gm.game.get("commence_time", ""),
                "blocks": blocks,
            })
        if len(results) >= MAX_GAMES:
            break
    results.sort(key=lambda r: r["commence_time"])
    return results


def _blocks(gm: GameMarkets, pq: ParsedQuery, focus: str | None) -> list[dict]:
    by_market: dict[str, list[tuple]] = {}
    for gkey, by_book in gm.groups.items():
        market = gkey[0]
        if pq.market and market != pq.market:
            continue
        if pq.points and (market == "h2h" or abs(gkey[1]) not in pq.points):
            continue
        by_market.setdefault(market, []).append((gkey, by_book))

    blocks = []
    for market in ("h2h", "spreads", "totals"):
        # Main lines first: the ones the most books quote.
        groups = sorted(by_market.get(market, []), key=lambda g: len(g[1]), reverse=True)[:LINES_PER_MARKET]
        for gkey, by_book in groups:
            fair = fair_line(gm, gkey)
            probs = fair.probs if fair else {}
            sides = sorted(gm.required[gkey], key=lambda s: (s != focus, s))
            if focus and focus in sides:
                sides = [focus]
            blocks.append({
                "market": MARKET_NAMES[market],
                "sharp_books": list(fair.titles) if fair else [],
                "sides": [_side(gm, gkey, by_book, s, probs.get(s)) for s in sides],
            })
    return blocks


def _side(gm: GameMarkets, gkey: tuple, by_book: dict, selection: str, fair_prob: float | None) -> dict:
    quotes = sorted((q[selection] for q in by_book.values() if selection in q), key=lambda q: q.decimal, reverse=True)
    rows = [{
        "book_title": q.book_title,
        "odds": q.american,
        "implied": 1 / q.decimal,
        "ev_pct": expected_value(fair_prob, q.decimal) * 100 if fair_prob else None,
        "sharp": q.book in SHARP_BOOKS,
        # Exchange commission lowers the effective price below the posted odds.
        "after_fee": abs(q.decimal - american_to_decimal(q.american)) > 1e-9,
    } for q in quotes]
    return {
        "pick": label(gkey[0], selection, quotes[0].point if quotes else None),
        "fair_prob": fair_prob,
        "best": rows[0] if rows else None,
        "rows": rows,
    }


def suggestions(grouped: list[GameMarkets]) -> list[str]:
    teams = {t for gm in grouped for t in (gm.game.get("home_team", ""), gm.game.get("away_team", "")) if t}
    return sorted(teams)

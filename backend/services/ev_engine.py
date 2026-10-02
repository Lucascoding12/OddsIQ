"""
+EV engine — prices soft-book odds against a sharp-book "true" line.

Method, per market group (same game, market and line):
  1. Each sharp book quoting the full outcome set is de-vigged (power method)
     into fair probabilities.
  2. Those are blended by SHARP_WEIGHTS into one fair probability per outcome.
  3. Every soft-book price is scored:  EV = fair_prob × decimal − 1.
     Positive EV means the soft book is paying more than the outcome is worth.

Why these sharp books (and weights):
  Pinnacle is the market standard for true odds: thin margins, high limits,
  and it doesn't limit winners, so its lines absorb sharp money fastest.
  Independent sharpness rankings (Pikkit's book-weighting study across NFL,
  NBA, MLB) put Pinnacle, Circa, BookMaker and BetOnline at the top and
  BetMGM at the bottom. Circa and BookMaker aren't in The Odds API feed.
  LowVig is BetOnline's low-margin sister site, so the two are one *family*
  and count once. Novig and ProphetX are US exchanges whose prices are set by
  bettors, which keeps margins near zero.

Unlike arbs, +EV bets can lose individually; the edge only shows up over
many bets. Hence Kelly sizing instead of balanced stakes.
"""
from dataclasses import dataclass

from services.markets import GameMarkets, Quote, ScanConfig, label
from services.odds_math import (
    decimal_to_american,
    devig_power,
    expected_value,
    kelly_fraction,
    round_stakes,
)

SHARP_WEIGHTS: dict[str, float] = {
    "pinnacle": 1.0,
    "betonlineag": 0.6,
    "lowvig": 0.6,
    "novig": 0.5,
    "prophetx": 0.4,
    "betfair_ex_eu": 0.6,
    "betfair_ex_uk": 0.6,
}
# Books that copy one another's lines — only the first present counts.
SHARP_FAMILIES: dict[str, str] = {"lowvig": "betonlineag"}

# Edges this large usually mean a stale soft line or a sharp quote we
# matched wrongly, not free money. Shown, but flagged.
SUSPICIOUS_EV_PCT = 10.0


@dataclass(slots=True)
class EvBet:
    id: str
    game_id: str
    sport_key: str
    sport_title: str
    home_team: str
    away_team: str
    commence_time: str
    market: str
    line: float | None
    selection: str
    point: float | None
    fair_prob: float
    sharp_books: tuple[str, ...]  # titles
    # every soft quote on this outcome with EV ≥ the scan floor, best first
    offers: tuple[tuple[Quote, float], ...]
    suspicious: bool

    @property
    def ev_pct(self) -> float:
        return self.offers[0][1] * 100


def fair_line(gm: GameMarkets, gkey: tuple) -> tuple[dict[str, float], tuple[str, ...]] | None:
    """Weighted blend of de-vigged sharp prices for one group, or None without a sharp quote."""
    complete = gm.complete_books(gkey)
    used: dict[str, dict[str, Quote]] = {}
    for book, quotes in complete.items():
        if book not in SHARP_WEIGHTS:
            continue
        family = SHARP_FAMILIES.get(book, book)
        if family != book and family in complete:
            continue
        used[book] = quotes
    if not used:
        return None

    selections = sorted(gm.required[gkey])
    blended = dict.fromkeys(selections, 0.0)
    total_weight = 0.0
    for book, quotes in used.items():
        weight = SHARP_WEIGHTS[book]
        fair = devig_power([quotes[s].decimal for s in selections])
        for s, p in zip(selections, fair):
            blended[s] += weight * p
        total_weight += weight
    titles = tuple(next(iter(q.values())).book_title for q in used.values())
    return {s: p / total_weight for s, p in blended.items()}, titles


def ev_from_grouped(gm: GameMarkets, cfg: ScanConfig, min_ev_pct: float = 0.0) -> list[EvBet]:
    game = gm.game
    results: list[EvBet] = []
    for gkey, by_book in gm.groups.items():
        fair = fair_line(gm, gkey)
        if fair is None:
            continue
        probs, sharp_titles = fair
        market, line = gkey[0], gkey[1]

        for selection, p in probs.items():
            offers = []
            for book, quotes in by_book.items():
                if book in SHARP_WEIGHTS or selection not in quotes:
                    continue
                q = quotes[selection]
                ev = expected_value(p, q.decimal)
                if ev * 100 >= min_ev_pct:
                    offers.append((q, ev))
            if not offers:
                continue
            offers.sort(key=lambda o: o[1], reverse=True)
            point = offers[0][0].point
            results.append(EvBet(
                id=f"ev:{game.get('id')}:{market}:{'' if line is None else f'{line:g}'}:{selection}",
                game_id=game.get("id", ""),
                sport_key=game.get("sport_key", ""),
                sport_title=game.get("sport_title", game.get("sport_key", "")),
                home_team=game.get("home_team", ""),
                away_team=game.get("away_team", ""),
                commence_time=game.get("commence_time") or "",
                market=market,
                line=line,
                selection=selection,
                point=point,
                fair_prob=p,
                sharp_books=sharp_titles,
                offers=tuple(offers),
                suspicious=offers[0][1] * 100 > SUSPICIOUS_EV_PCT,
            ))
    return results


def ev_payload(
    bet: EvBet,
    offers: list[tuple[Quote, float]],
    bankroll: float,
    kelly_multiplier: float,
    round_to: float,
    first_seen: str | None,
) -> dict:
    """`offers` is the caller's book-filtered subset, best first and non-empty."""
    best, ev = offers[0]
    raw_stake = bankroll * kelly_multiplier * kelly_fraction(bet.fair_prob, best.decimal)
    stake = round_stakes([raw_stake], round_to)[0] if raw_stake > 0 else 0.0
    return {
        "id": bet.id,
        "game_id": bet.game_id,
        "sport_key": bet.sport_key,
        "sport_title": bet.sport_title,
        "home_team": bet.home_team,
        "away_team": bet.away_team,
        "commence_time": bet.commence_time,
        "market": bet.market,
        "line": bet.line,
        "pick": label(bet.market, bet.selection, bet.point),
        "fair_prob": round(bet.fair_prob, 4),
        "fair_odds": decimal_to_american(1 / bet.fair_prob),
        "sharp_books": list(bet.sharp_books),
        "ev_pct": round(ev * 100, 2),
        "book": best.book,
        "book_title": best.book_title,
        "odds": best.american,
        "stake": round(stake, 2),
        "expected_profit": round(stake * ev, 2),
        "suspicious": bet.suspicious,
        "first_seen": first_seen,
        "also": [
            {"book": q.book, "book_title": q.book_title, "odds": q.american, "ev_pct": round(e * 100, 2)}
            for q, e in offers[1:]
        ],
    }

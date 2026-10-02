"""
+EV engine — prices soft-book odds against a sharp-book "true" line.

Method, per market group (same game, market and line):
  1. Each sharp book quoting the full outcome set is de-vigged (power method)
     into fair probabilities.
  2. Those are blended by SHARP_WEIGHTS into one fair probability per outcome.
  3. Every soft-book price is scored:  EV = fair_prob × decimal − 1.
     Positive EV means the soft book is paying more than the outcome is worth.

Why these sharp sources (and weights):
  No single venue is clearly sharpest. A 5,333-game study (Northwestern,
  2025–26) found Kalshi, Polymarket and the sportsbook consensus within
  ±0.001 Brier score of each other at the close, holding with Pinnacle as
  the benchmark. So the fair line blends several independent sources rather
  than trusting one.
  - Pinnacle: longest track record (closing-line r² ≈ 0.997 vs results over
    ~400k soccer games), high limits, doesn't limit winners → highest weight.
  - Kalshi, Polymarket: as accurate as books at the close, but slightly
    overconfident (calibration slope ≈ 0.955), so their probabilities are
    pulled toward 50% before blending (PREDICTION_MARKET_SLOPE).
  - BetOnline: top-ranked in Pikkit's sharpness study. LowVig copies its
    lines exactly, so it's a family member that never counts twice.
  - Novig, ProphetX: US exchanges with near-zero margins but thinner volume.

Confidence:
  Sharp sources disagree by ~1.4 probability points on a typical market,
  which is as large as most edges. So each bet also gets a worst-case EV
  (priced against the least favorable sharp source) and a confidence level:
    strong  3+ independent sources, and every one says the bet is +EV
    fair    2+ sources, every one says +EV
    thin    one source, or the sources disagree on whether it's +EV

Unlike arbs, +EV bets can lose individually; the edge only shows up over
many bets. Hence Kelly sizing instead of balanced stakes.
"""
import math
from dataclasses import dataclass
from typing import NamedTuple

from services.markets import GameMarkets, Quote, ScanConfig, label
from services.odds_math import (
    american_to_decimal,
    decimal_to_american,
    devig_power,
    expected_value,
    kelly_fraction,
    round_stakes,
)

SHARP_WEIGHTS: dict[str, float] = {
    "pinnacle": 1.0,
    "kalshi": 0.9,
    "polymarket": 0.7,
    "betonlineag": 0.6,
    "lowvig": 0.6,
    "novig": 0.5,
    "prophetx": 0.4,
    "betfair_ex_eu": 0.6,
    "betfair_ex_uk": 0.6,
}
# Calibration slopes from the Northwestern study: prediction-market prices are
# a little too extreme, so their log-odds are scaled down before blending.
PREDICTION_MARKET_SLOPE: dict[str, float] = {"kalshi": 0.956, "polymarket": 0.954}
# Books that copy one another's lines — only the first present counts.
SHARP_FAMILIES: dict[str, str] = {"lowvig": "betonlineag"}

# Edges this large usually mean a stale soft line or a sharp quote we
# matched wrongly, not free money. Shown, but flagged.
SUSPICIOUS_EV_PCT = 10.0


class FairLine(NamedTuple):
    probs: dict[str, float]                   # blended fair probability per outcome
    titles: tuple[str, ...]                   # sharp sources used
    per_source: dict[str, dict[str, float]]   # source title → outcome → fair probability


def _recalibrate(probs: list[float], slope: float) -> list[float]:
    """Scale log-odds by `slope` (< 1 pulls toward 50%), then renormalize."""
    adjusted = [1 / (1 + math.exp(-slope * math.log(p / (1 - p)))) for p in probs]
    total = sum(adjusted)
    return [a / total for a in adjusted]


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
    # (source title, that source's fair probability for this outcome)
    sharp_probs: tuple[tuple[str, float], ...] = ()

    @property
    def fair_prob_low(self) -> float:
        """The least favorable single sharp source's view of this outcome."""
        return min((p for _, p in self.sharp_probs), default=self.fair_prob)

    @property
    def ev_pct(self) -> float:
        return self.offers[0][1] * 100

    def worst_case_ev(self, decimal: float) -> float:
        return expected_value(self.fair_prob_low, decimal)

    @property
    def confidence(self) -> str:
        agrees = self.worst_case_ev(self.offers[0][0].decimal) > 0
        if agrees and len(self.sharp_books) >= 3:
            return "strong"
        if agrees and len(self.sharp_books) >= 2:
            return "fair"
        return "thin"


def fair_line(gm: GameMarkets, gkey: tuple) -> FairLine | None:
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
    per_source: dict[str, dict[str, float]] = {}
    total_weight = 0.0
    for book, quotes in used.items():
        weight = SHARP_WEIGHTS[book]
        # Posted prices, not fee-adjusted: a venue's fee is its cost, not its opinion.
        fair = devig_power([american_to_decimal(quotes[s].american) for s in selections])
        if book in PREDICTION_MARKET_SLOPE:
            fair = _recalibrate(fair, PREDICTION_MARKET_SLOPE[book])
        for s, p in zip(selections, fair):
            blended[s] += weight * p
        total_weight += weight
        per_source[next(iter(quotes.values())).book_title] = dict(zip(selections, fair))
    return FairLine({s: p / total_weight for s, p in blended.items()}, tuple(per_source), per_source)


def ev_from_grouped(gm: GameMarkets, cfg: ScanConfig, min_ev_pct: float = 0.0) -> list[EvBet]:
    game = gm.game
    results: list[EvBet] = []
    for gkey, by_book in gm.groups.items():
        fair = fair_line(gm, gkey)
        if fair is None:
            continue
        probs, sharp_titles = fair.probs, fair.titles
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
                sharp_probs=tuple((t, src[selection]) for t, src in fair.per_source.items()),
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
        "worst_case_ev_pct": round(bet.worst_case_ev(best.decimal) * 100, 2),
        "confidence": bet.confidence,
        "sharp_detail": {t: round(p, 4) for t, p in bet.sharp_probs},
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

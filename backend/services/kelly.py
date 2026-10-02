"""
Kelly criterion math for the Kelly page.

Kelly picks the bet size that maximizes the long-run growth rate of a
bankroll: f* = (p·d − 1) / (d − 1), with p the true win probability and d the
decimal odds. The growth rate per bet at stake fraction f is

    g(f) = p·ln(1 + f·(d − 1)) + (1 − p)·ln(1 − f)

which peaks at f*, falls back to zero near 2·f*, and goes negative beyond —
over-betting a real edge still loses money in the long run.

Fractional Kelly (bet c·f*) trades a little growth for much smaller swings.
For continuous Kelly betting, the chance of the bankroll *ever* falling to a
fraction x of its starting value is x^(2/c − 1) (Thorp). It's an idealized
model, but it shows the shape: halving the bet cuts a 50% drawdown chance
from 1 in 2 to 1 in 8.
"""
import math
from dataclasses import dataclass

from services.odds_math import kelly_fraction, round_stakes

FRACTIONS: tuple[tuple[str, float], ...] = (("Full", 1.0), ("Half", 0.5), ("Quarter", 0.25), ("Tenth", 0.1))


def growth_rate(f: float, p: float, decimal: float) -> float:
    """Expected log growth per bet when staking fraction f of the bankroll."""
    if f <= 0:
        return 0.0
    if f >= 1:
        return -math.inf
    return p * math.log1p(f * (decimal - 1)) + (1 - p) * math.log1p(-f)


def drawdown_chance(kelly_multiple: float, floor: float = 0.5) -> float:
    """Chance of ever dropping to `floor` × bankroll when betting kelly_multiple × Kelly."""
    if kelly_multiple >= 2:
        return 1.0
    return floor ** (2 / kelly_multiple - 1)


def bets_to_double(growth: float) -> float | None:
    """Expected number of bets to double the bankroll at this growth rate."""
    return math.log(2) / growth if growth > 0 else None


@dataclass
class SizingRow:
    name: str
    multiple: float
    fraction: float
    stake: float
    growth_pct: float
    halving_chance: float
    bets_to_double: float | None


def sizing_table(p: float, decimal: float, bankroll: float, round_to: float = 0.0) -> list[SizingRow]:
    full = kelly_fraction(p, decimal)
    rows = []
    for name, multiple in FRACTIONS:
        fraction = full * multiple
        g = growth_rate(fraction, p, decimal)
        stake = round_stakes([bankroll * fraction], round_to)[0] if fraction > 0 else 0.0
        rows.append(SizingRow(name, multiple, fraction, stake, g * 100, drawdown_chance(multiple), bets_to_double(g)))
    return rows


def growth_curve(p: float, decimal: float, points: int = 80) -> list[tuple[float, float]]:
    """(fraction, growth %) from 0 to 2.5× Kelly — wide enough to show growth turning negative."""
    full = kelly_fraction(p, decimal)
    if full <= 0:
        return []
    top = min(0.99, full * 2.5)
    out = []
    for i in range(points + 1):
        f = top * i / points
        out.append((f, growth_rate(f, p, decimal) * 100))
    return out


@dataclass
class SheetRow:
    label: str
    book_title: str
    odds: int
    fair_prob: float
    ev_pct: float
    confidence: str
    kelly_fraction: float
    stake: float


def kelly_sheet(bets: list[dict], bankroll: float, multiple: float, max_exposure: float,
                round_to: float, conservative: bool) -> tuple[list[SheetRow], float]:
    """
    Kelly stakes for every live +EV bet at once. Kelly assumes one bet at a
    time; with many open together, the total is capped at max_exposure of the
    bankroll and every stake is scaled down by the same factor.
    Returns the rows and the scale factor applied (1.0 when under the cap).
    """
    raw = []
    for b in bets:
        p = b["fair_prob_low"] if conservative else b["fair_prob"]
        f = kelly_fraction(p, b["decimal"]) * multiple
        if f > 0:
            raw.append((b, p, f))
    total = sum(f for _, _, f in raw)
    scale = min(1.0, max_exposure / total) if total > 0 else 1.0
    rows = [
        SheetRow(b["label"], b["book_title"], b["odds"], p, b["ev_pct"], b["confidence"], f * scale,
                 round_stakes([bankroll * f * scale], round_to)[0])
        for b, p, f in raw
    ]
    rows.sort(key=lambda r: r.stake, reverse=True)
    return rows, scale

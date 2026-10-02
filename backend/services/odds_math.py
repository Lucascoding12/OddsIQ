"""
Pure odds conversions and stake math. No I/O — everything here is unit-tested
and shared by the arb engine, the sharp endpoints and the manual calculator.

Conventions:
  - "decimal" odds include the stake: +150 American == 2.5 decimal.
  - An arb exists when the sum of inverse decimal odds across a complete,
    mutually exclusive set of outcomes is < 1.
"""
import math


def american_to_decimal(american: float) -> float:
    if american > 0:
        return american / 100 + 1
    return 100 / -american + 1


def decimal_to_american(decimal: float) -> int:
    if decimal >= 2:
        return round((decimal - 1) * 100)
    return round(-100 / (decimal - 1))


def implied_prob(american: float) -> float:
    return 1 / american_to_decimal(american)


def apply_commission(decimal: float, commission: float) -> float:
    """Exchanges charge commission on net winnings, which shrinks the effective price."""
    return 1 + (decimal - 1) * (1 - commission)


def no_vig_probs(americans: list[float]) -> list[float]:
    """Normalize implied probabilities so they sum to 1 (removes the book's margin)."""
    probs = [implied_prob(a) for a in americans]
    total = sum(probs)
    return [p / total for p in probs]


def arb_return_pct(decimals: list[float]) -> float:
    """
    Guaranteed return on total stake, in percent. Negative = no arb.
    1/sum(1/d) is the payout per $1 staked when stakes are balanced.
    """
    return (1 / sum(1 / d for d in decimals) - 1) * 100


def balanced_stakes(decimals: list[float], bankroll: float) -> list[float]:
    """Split `bankroll` so every outcome pays out the same amount."""
    inv = [1 / d for d in decimals]
    total = sum(inv)
    return [bankroll * i / total for i in inv]


def round_stakes(stakes: list[float], round_to: float) -> list[float]:
    """
    Round stakes to a betting-friendly increment. Odd-cent stakes are a classic
    arber tell that gets accounts limited, so whole dollars are the usual choice.
    """
    if round_to <= 0:
        return [round(s, 2) for s in stakes]
    return [max(round_to, math.floor(s / round_to + 0.5) * round_to) for s in stakes]


def guaranteed_profit(stakes: list[float], decimals: list[float]) -> float:
    """Worst-case profit across outcomes for a given stake split."""
    return min(s * d for s, d in zip(stakes, decimals)) - sum(stakes)

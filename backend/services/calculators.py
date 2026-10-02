"""
Betting calculators — ported from the Next.js calculator page.

Each calculator is data (fields, copy) plus a pure compute function that takes
the raw form strings and returns metrics and an optional table. The UI renders
any calculator generically, so adding one means adding one entry here.

Corrections vs. the original TypeScript versions:
  - Arbitrage profit is 1/Σp − 1 (return on stake), not 1 − Σp.
  - Point spread probability is for the team *at* the spread, so a −3.5
    favorite comes out above 50%, matching the worked example.
  - Bonus bet conversion hedges the other side at a real price instead of
    assuming a fixed lay factor.
"""
import itertools
import math
import re
from dataclasses import dataclass, field
from typing import Callable

from services.odds_math import (
    american_to_decimal,
    best_rounded_stakes,
    decimal_to_american,
    devig_power,
    guaranteed_profit,
    kelly_fraction,
)


class CalcError(ValueError):
    """Bad user input; the message is shown in place of results."""


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    default: str
    options: tuple[tuple[str, str], ...] = ()  # (value, label) → rendered as a select


@dataclass
class Result:
    metrics: list[tuple[str, str, str | None]] = field(default_factory=list)  # label, value, tone
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Calculator:
    slug: str
    name: str
    description: str
    usage: str
    example: str
    fields: tuple[Field, ...]
    compute: Callable[[dict[str, str]], Result]


# ── Parsing & formatting ─────────────────────────────────────────────────────

def _num(raw: str, label: str) -> float:
    try:
        return float(raw.replace("$", "").replace(",", "").replace("%", "").strip())
    except ValueError:
        raise CalcError(f"{label} needs a number.") from None


def _odds(raw: str, label: str = "Odds") -> float:
    value = _num(raw, label)
    if -100 < value < 100:
        raise CalcError(f"{label} must be American odds: −100 or lower, or +100 or higher.")
    return value


def _odds_list(raw: str, label: str = "Odds", minimum: int = 2) -> list[float]:
    parts = [p for p in re.split(r"[,\s/]+", raw.strip()) if p]
    if len(parts) < minimum:
        raise CalcError(f"Enter at least {minimum} odds separated by commas, e.g. -110, +105.")
    return [_odds(p, label) for p in parts]


def _fmt_odds(american: float) -> str:
    if not math.isfinite(american):
        return "—"
    return f"{round(american):+d}"


def _pct(x: float, places: int = 2) -> str:
    return f"{x * 100:.{places}f}%"


def _money(x: float) -> str:
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def _tone(x: float) -> str | None:
    return "good" if x > 0 else "bad" if x < 0 else None


def _fair_american(p: float) -> float:
    if p <= 0 or p >= 1:
        return math.inf
    return decimal_to_american(1 / p)


def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ── Calculators ──────────────────────────────────────────────────────────────

def implied(f: dict[str, str]) -> Result:
    o = _odds(f["odds"])
    d = american_to_decimal(o)
    return Result(metrics=[
        ("Implied probability", _pct(1 / d), None),
        ("Decimal odds", f"{d:.3f}", None),
        ("Break-even win rate", _pct(1 / d), None),
    ])


def no_vig(f: dict[str, str]) -> Result:
    odds = _odds_list(f["odds"])
    decimals = [american_to_decimal(o) for o in odds]
    implied_p = [1 / d for d in decimals]
    total = sum(implied_p)
    proportional = [p / total for p in implied_p]
    power = devig_power(decimals)
    return Result(
        metrics=[("Market hold", _pct(total - 1), None), ("Sides", str(len(odds)), None)],
        headers=["Side", "Odds", "Implied", "Fair (proportional)", "Fair (power)", "Fair odds"],
        rows=[
            [str(i + 1), _fmt_odds(o), _pct(p), _pct(pp), _pct(pw), _fmt_odds(_fair_american(pw))]
            for i, (o, p, pp, pw) in enumerate(zip(odds, implied_p, proportional, power))
        ],
    )


def ev(f: dict[str, str]) -> Result:
    stake = _num(f["stake"], "Wager")
    o = _odds(f["odds"])
    p = _num(f["win_pct"], "Win probability") / 100
    d = american_to_decimal(o)
    profit = stake * (d - 1)
    value = p * profit - (1 - p) * stake
    return Result(metrics=[
        ("Expected value", _money(value), _tone(value)),
        ("ROI", _pct(value / stake if stake else 0), _tone(value)),
        ("Profit if win", _money(profit), None),
        ("Break-even win rate", _pct(1 / d), None),
    ])


def kelly(f: dict[str, str]) -> Result:
    mult = _num(f["multiplier"], "Kelly multiplier")
    o = _odds(f["odds"])
    p = _num(f["win_pct"], "Win %") / 100
    bankroll = _num(f["bankroll"], "Bankroll")
    d = american_to_decimal(o)
    full = kelly_fraction(p, d)
    edge = p * d - 1
    return Result(metrics=[
        ("Edge", _pct(edge), _tone(edge)),
        ("Full Kelly", _pct(full), None),
        ("Fraction to bet", _pct(full * mult), _tone(full)),
        ("Amount to wager", _money(full * mult * bankroll), _tone(full)),
    ])


def arbitrage(f: dict[str, str]) -> Result:
    odds = _odds_list(f["odds"])
    bankroll = _num(f["bankroll"], "Total stake")
    round_to = _num(f["round_to"], "Round to")
    decimals = [american_to_decimal(o) for o in odds]
    ret = 1 / sum(1 / d for d in decimals) - 1
    stakes = best_rounded_stakes(decimals, bankroll, round_to)
    profit = guaranteed_profit(stakes, decimals)
    return Result(
        metrics=[
            ("Arb?", "Yes" if ret > 0 else "No", _tone(ret)),
            ("Return", _pct(ret), _tone(ret)),
            ("Guaranteed profit", _money(profit), _tone(profit)),
            ("Total staked", _money(sum(stakes)), None),
        ],
        headers=["Leg", "Odds", "Stake", "Payout if it wins"],
        rows=[[str(i + 1), _fmt_odds(o), _money(s), _money(s * d)]
              for i, (o, s, d) in enumerate(zip(odds, stakes, decimals))],
    )


def clv(f: dict[str, str]) -> Result:
    bet = _odds(f["bet_odds"], "Odds you bet")
    close = _odds(f["closing_odds"], "Closing odds")
    bet_d, close_d = american_to_decimal(bet), american_to_decimal(close)
    price_edge = bet_d / close_d - 1
    prob_edge = 1 / close_d - 1 / bet_d
    verdict = "Beat the close" if price_edge > 0 else "Behind the close" if price_edge < 0 else "At the close"
    return Result(metrics=[
        ("CLV (price)", f"{price_edge * 100:+.2f}%", _tone(price_edge)),
        ("CLV (probability points)", f"{prob_edge * 100:+.2f}", _tone(prob_edge)),
        ("Verdict", verdict, _tone(price_edge)),
    ])


def hold(f: dict[str, str]) -> Result:
    odds = _odds_list(f["odds"])
    implied_p = [1 / american_to_decimal(o) for o in odds]
    total = sum(implied_p)
    return Result(
        metrics=[
            ("Hold", _pct(total - 1), "bad" if total > 1 else "good"),
            ("Total implied", _pct(total), None),
            ("Book keeps per $100 bet (balanced action)", _money(100 * (1 - 1 / total)), None),
        ],
        headers=["Side", "Odds", "Implied"],
        rows=[[str(i + 1), _fmt_odds(o), _pct(p)] for i, (o, p) in enumerate(zip(odds, implied_p))],
    )


def vig(f: dict[str, str]) -> Result:
    odds = _odds_list(f["odds"])
    decimals = [american_to_decimal(o) for o in odds]
    fair = devig_power(decimals)
    implied_p = [1 / d for d in decimals]
    return Result(
        metrics=[("Total vig", _pct(sum(implied_p) - 1), None)],
        headers=["Side", "Odds", "Implied", "Fair", "Vig on this side"],
        rows=[[str(i + 1), _fmt_odds(o), _pct(p), _pct(fp), f"{(p - fp) * 100:.2f} pts"]
              for i, (o, p, fp) in enumerate(zip(odds, implied_p, fair))],
    )


def bonus_bet(f: dict[str, str]) -> Result:
    bonus = _num(f["bonus"], "Bonus amount")
    d_bonus = american_to_decimal(_odds(f["bonus_odds"], "Bonus bet odds"))
    d_hedge = american_to_decimal(_odds(f["hedge_odds"], "Hedge odds"))
    # Bonus pays only profit. Equalize: bonus wins → B(d1−1) − H ; hedge wins → H(d2−1)
    hedge = bonus * (d_bonus - 1) / d_hedge
    cash = hedge * (d_hedge - 1)
    notes = []
    if 1 / d_bonus + 1 / d_hedge < 1:
        notes.append("These two prices would be an arb on their own. Make sure they're opposite sides of the same market.")
    return Result(notes=notes, metrics=[
        ("Hedge stake (other side, other book)", _money(hedge), None),
        ("Guaranteed cash", _money(cash), _tone(cash)),
        ("Conversion rate", _pct(cash / bonus if bonus else 0, 1), "good" if bonus and cash / bonus >= 0.6 else None),
    ])


def converter(f: dict[str, str]) -> Result:
    raw = f["value"].strip()
    try:
        if raw.endswith("%"):
            d = 100 / _num(raw, "Probability")
        elif "/" in raw:
            num, den = raw.split("/", 1)
            d = _num(num, "Fraction") / _num(den, "Fraction") + 1
        else:
            value = _num(raw, "Odds")
            d = value if 1 < value < 100 and "." in raw else american_to_decimal(_odds(raw))
    except ZeroDivisionError:
        raise CalcError("That value can't be converted.") from None
    if d <= 1:
        raise CalcError("Odds must pay more than the stake.")
    frac = _fraction(d - 1)
    return Result(metrics=[
        ("American", _fmt_odds(decimal_to_american(d)), None),
        ("Decimal", f"{d:.3f}", None),
        ("Fractional", frac, None),
        ("Implied probability", _pct(1 / d), None),
    ])


def _fraction(x: float) -> str:
    best = min(((round(x * den), den) for den in range(1, 101)), key=lambda nd: abs(nd[0] / nd[1] - x))
    g = math.gcd(*best)
    return f"{best[0] // g}/{best[1] // g}"


def parlay(f: dict[str, str]) -> Result:
    odds = _odds_list(f["odds"], minimum=2)
    stake = _num(f["stake"], "Stake")
    decimals = [american_to_decimal(o) for o in odds]
    combined = math.prod(decimals)
    return Result(
        metrics=[
            ("Parlay odds", _fmt_odds(decimal_to_american(combined)), None),
            ("Decimal", f"{combined:.3f}", None),
            ("Payout", _money(stake * combined), None),
            ("Implied chance all hit", _pct(1 / combined), None),
        ],
        headers=["Leg", "Odds", "Decimal"],
        rows=[[str(i + 1), _fmt_odds(o), f"{d:.3f}"] for i, (o, d) in enumerate(zip(odds, decimals))],
    )


def prediction_market(f: dict[str, str]) -> Result:
    cents = _num(f["price"], "Price")
    if not 0 < cents < 100:
        raise CalcError("Price must be between 1¢ and 99¢.")
    fee = _num(f["fee_pct"], "Fee") / 100
    d = 100 / cents
    d_after = 1 + (d - 1) * (1 - fee)
    return Result(metrics=[
        ("Implied probability", _pct(cents / 100, 1), None),
        ("American odds", _fmt_odds(decimal_to_american(d)), None),
        ("Decimal odds", f"{d:.3f}", None),
        ("After fee (American)", _fmt_odds(decimal_to_american(d_after)), None),
    ])


SPREAD_SIGMA = {"nfl": 13.45, "ncaaf": 16.0, "nba": 11.0, "ncaab": 10.5, "mlb": 1.5, "nhl": 1.2}


def point_spread(f: dict[str, str]) -> Result:
    spread = _num(f["spread"], "Spread")
    sigma = SPREAD_SIGMA.get(f["sport"], 13.45)
    p = _normal_cdf(-spread / sigma)
    return Result(metrics=[
        ("Win probability", _pct(p), None),
        ("Fair moneyline", _fmt_odds(_fair_american(p)), None),
        ("Opponent win probability", _pct(1 - p), None),
        ("Opponent fair moneyline", _fmt_odds(_fair_american(1 - p)), None),
    ])


def poisson(f: dict[str, str]) -> Result:
    lam = _num(f["lam"], "Expected count")
    k = int(_num(f["k"], "Count"))
    if lam <= 0 or k < 0:
        raise CalcError("Expected count must be positive and count can't be negative.")
    probs = [math.exp(-lam) * lam ** i / math.factorial(i) for i in range(max(10, k + 3) + 1)]
    under = sum(probs[:k])
    exactly = probs[k]
    return Result(
        metrics=[
            (f"Exactly {k}", _pct(exactly, 2), None),
            (f"Under {k}", _pct(under), None),
            (f"Over {k}", _pct(1 - under - exactly), None),
            (f"Over {k - 0.5:g} fair odds", _fmt_odds(_fair_american(1 - under)), None),
        ],
        headers=["Count", "Probability", "Fair odds"],
        rows=[[str(i), _pct(p), _fmt_odds(_fair_american(p))] for i, p in enumerate(probs)],
    )


def round_robin(f: dict[str, str]) -> Result:
    odds = _odds_list(f["odds"], minimum=3)
    size = int(_num(f["size"], "Parlay size"))
    stake = _num(f["stake"], "Stake per parlay")
    if not 2 <= size <= len(odds):
        raise CalcError(f"Parlay size must be between 2 and {len(odds)}.")
    decimals = [american_to_decimal(o) for o in odds]
    combos = list(itertools.combinations(range(len(odds)), size))
    payouts = [stake * math.prod(decimals[i] for i in c) for c in combos]
    rows = []
    for wins in range(size, len(odds) + 1):
        # Best case: the highest-priced legs are the ones that win.
        winners = set(sorted(range(len(odds)), key=lambda i: decimals[i], reverse=True)[:wins])
        cashed = [p for c, p in zip(combos, payouts) if winners.issuperset(c)]
        rows.append([str(wins), str(len(cashed)), _money(sum(cashed) - stake * len(combos))])
    return Result(
        metrics=[
            ("Parlays", str(len(combos)), None),
            ("Total stake", _money(stake * len(combos)), None),
            ("Max payout", _money(sum(payouts)), None),
            ("Average parlay payout", _money(sum(payouts) / len(payouts)), None),
        ],
        headers=["Legs that win", "Parlays cashed", "Net (best case)"],
        rows=rows,
    )


CALCULATORS: tuple[Calculator, ...] = (
    Calculator("implied", "Implied probability",
        "Convert American odds to the sportsbook's implied win probability.",
        "Every American odds line contains an embedded win probability, the rate the book needs you to lose at to make money. If the book's implied probability is lower than your own estimate, you may have an edge.",
        "Chiefs are −150. Implied probability is 60.0%. If you think they win 65% of the time, the bet has positive EV.",
        (Field("odds", "American odds", "-150"),), implied),
    Calculator("no-vig", "No-vig fair odds",
        "Strip the sportsbook margin to find the true fair odds for each side.",
        "Books inflate the implied probabilities on both sides so they profit either way. Removing that margin leaves the market's true estimate. The power method takes more margin off longshots, which matches how books actually shade prices.",
        "−110 / −110: each side is 52.38% implied (104.76% total). Fair odds are +100 each; the 4.76% was the book's cut.",
        (Field("odds", "Odds for every side", "-110, -110"),), no_vig),
    Calculator("ev", "Expected value",
        "Calculate the expected profit of a bet given your true probability estimate.",
        "EV says whether a bet is profitable in the long run. A single bet can win or lose; EV is about what happens over hundreds of bets.",
        "$100 at +110 with a 60% win chance: EV = 0.60 × $110 − 0.40 × $100 = +$26.",
        (Field("stake", "Wager ($)", "100"), Field("odds", "Odds", "+110"), Field("win_pct", "Win probability (%)", "60")), ev),
    Calculator("kelly", "Kelly criterion",
        "Find the optimal fraction of your bankroll to wager based on your edge.",
        "Kelly sizes bets by edge and price. Overbetting risks ruin even with a real edge; most sharp bettors use quarter or half Kelly to cut variance.",
        "$5,000 bankroll, +110, 60% win chance: full Kelly is 23.6% ($1,182). Quarter Kelly is $295.",
        (Field("multiplier", "Kelly multiplier", "0.25"), Field("odds", "Odds", "+110"),
         Field("win_pct", "Win probability (%)", "60"), Field("bankroll", "Bankroll ($)", "5000")), kelly),
    Calculator("arbitrage", "Arbitrage",
        "Check a set of prices for guaranteed profit and get exact stakes.",
        "An arb exists when the combined implied probability across all outcomes at different books is under 100%. Windows close fast, and books limit accounts that take them.",
        "DraftKings Chiefs +105, FanDuel Bills +103: 48.8% + 49.3% = 98.1%. That's a 2.0% guaranteed return.",
        (Field("odds", "Best odds for each outcome", "+105, +103"), Field("bankroll", "Total stake ($)", "1000"),
         Field("round_to", "Round stakes to ($)", "1")), arbitrage),
    Calculator("clv", "Closing line value",
        "Measure how sharp your bet was by comparing it to the closing line.",
        "Beating the closing line is the best long-run sign you're a sharp bettor. Consistently negative CLV means you're betting into the public.",
        "You bet the Celtics at −180 and they closed −210. You got a 5.4% better price than the close.",
        (Field("bet_odds", "Odds you bet", "-180"), Field("closing_odds", "Closing odds", "-210")), clv),
    Calculator("hold", "Hold",
        "Calculate the sportsbook's total margin across all sides of a market.",
        "Hold is the sum of all implied probabilities minus 100%. Lower-hold books like Pinnacle are better places to bet.",
        "−110 / −110 has a 4.76% hold. Pinnacle at −105 / −105 holds only 2.44%.",
        (Field("odds", "Odds for every side", "-110, -110"),), hold),
    Calculator("vig", "Vig by side",
        "See how much of the juice each side of a market carries.",
        "Vig isn't always split evenly. The side carrying more of it is the worse bet at that book.",
        "−115 / −105: total vig is 4.7%, and the −115 side carries most of it.",
        (Field("odds", "Odds for every side", "-115, -105"),), vig),
    Calculator("bonus-bet", "Bonus bet conversion",
        "Turn a bonus bet into guaranteed cash by hedging the other side.",
        "Bonus bets pay only the profit. Put the bonus on a longshot and hedge the other side at a different book to lock in cash whichever side wins. Longer odds convert better.",
        "$100 bonus at +200, hedge the other side at −240 at another book: hedge $141 and keep $59 either way, a 59% conversion.",
        (Field("bonus", "Bonus amount ($)", "100"), Field("bonus_odds", "Odds for the bonus bet", "+200"),
         Field("hedge_odds", "Odds on the other side", "-240")), bonus_bet),
    Calculator("converter", "Odds converter",
        "Convert between American, decimal, fractional and probability.",
        "Type any format: +150, 2.50, 3/2 or 40%.",
        "Pinnacle shows 2.050 decimal, which is +105 American or 21/20 fractional.",
        (Field("value", "Odds in any format", "2.050"),), converter),
    Calculator("parlay", "Parlay",
        "Calculate combined odds and payout for a multi-leg parlay.",
        "All legs must win. Compare the true combined price with what the book offers to see how much extra margin they're taking.",
        "Three legs at −110: true odds are about +596. If the book pays +550, that's the extra cut.",
        (Field("odds", "Leg odds", "-110, -110, -110"), Field("stake", "Stake ($)", "10")), parlay),
    Calculator("prediction-market", "Prediction market",
        "Convert Kalshi or Polymarket prices to standard odds.",
        "Contracts trade in cents, where 65¢ means 65%. Convert to compare against sportsbook lines. Include the platform's fee to see the price you really get.",
        "Chiefs to win at 38¢ is 38%, or +163.",
        (Field("price", "Price (¢)", "38"), Field("fee_pct", "Fee on winnings (%)", "0")), prediction_market),
    Calculator("point-spread", "Point spread",
        "Estimate win probability and a fair moneyline from a point spread.",
        "Margin of victory is roughly normal around the spread. Each sport's spread of outcomes (σ) turns a line into a win probability.",
        "Chiefs −3.5 in the NFL (σ 13.45) win about 60.3% of the time, a fair moneyline near −152.",
        (Field("spread", "Spread", "-3.5"), Field("sport", "Sport", "nfl", options=(
            ("nfl", "NFL"), ("ncaaf", "College football"), ("nba", "NBA"),
            ("ncaab", "College basketball"), ("mlb", "MLB run line"), ("nhl", "NHL puck line")))), point_spread),
    Calculator("poisson", "Poisson",
        "Model goals, runs or scores from an expected rate.",
        "Poisson gives the chance of each exact count given an average rate. Use it to price totals and exact-score markets.",
        "A team averaging 1.8 goals: exactly 2 is 26.8%, under 2 is 46.3%.",
        (Field("lam", "Expected count (λ)", "1.8"), Field("k", "Count", "2")), poisson),
    Calculator("round-robin", "Round robin",
        "Generate every parlay combination from a set of picks and calculate payouts.",
        "A round robin builds every parlay of a given size from your picks. It costs more up front, but you can still cash when a leg or two loses.",
        "5 picks, 3-leg parlays at $10: 10 parlays, $100 total. If 4 of 5 win, 4 of the 10 parlays cash.",
        (Field("odds", "Leg odds", "-110, +120, -105, +150, -130"), Field("size", "Legs per parlay", "3"),
         Field("stake", "Stake per parlay ($)", "10")), round_robin),
)

BY_SLUG = {c.slug: c for c in CALCULATORS}


def run(calc: Calculator, values: dict[str, str]) -> tuple[Result | None, str | None]:
    """Compute with defaults filled in; returns (result, error message)."""
    filled = {fld.name: values.get(fld.name, fld.default) for fld in calc.fields}
    try:
        return calc.compute(filled), None
    except CalcError as exc:
        return None, str(exc)
    except (OverflowError, ZeroDivisionError):
        return None, "Those numbers are out of range."

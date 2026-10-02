"""Tests for the arb engine and the odds math it relies on."""
import unittest
from datetime import datetime

from services.arb_engine import ScanConfig, scan_game, scan_games, to_payload
from services.odds_math import (
    american_to_decimal,
    arb_return_pct,
    balanced_stakes,
    decimal_to_american,
    guaranteed_profit,
    round_stakes,
)

NOW = datetime.fromisoformat("2026-10-02T12:00:00+00:00").timestamp()
FRESH = "2026-10-02T11:59:00Z"
STALE = "2026-10-02T09:00:00Z"
FUTURE = "2026-10-02T23:00:00Z"
PAST = "2026-10-02T11:00:00Z"
OPEN = ScanConfig()


def _game(bookmakers: list[dict], commence: str = FUTURE) -> dict:
    return {
        "id": "g1",
        "sport_key": "baseball_mlb",
        "sport_title": "MLB",
        "home_team": "Yankees",
        "away_team": "Red Sox",
        "commence_time": commence,
        "bookmakers": bookmakers,
    }


def _book(key: str, markets: list[dict]) -> dict:
    return {"key": key, "title": key.upper(), "last_update": FRESH, "markets": markets}


def _h2h(prices: dict[str, int], updated: str = FRESH) -> dict:
    return {"key": "h2h", "last_update": updated,
            "outcomes": [{"name": n, "price": p} for n, p in prices.items()]}


def _spread(home_pt: float, home_px: int, away_pt: float, away_px: int) -> dict:
    return {"key": "spreads", "last_update": FRESH, "outcomes": [
        {"name": "Yankees", "price": home_px, "point": home_pt},
        {"name": "Red Sox", "price": away_px, "point": away_pt},
    ]}


def _total(point: float, over: int, under: int) -> dict:
    return {"key": "totals", "last_update": FRESH, "outcomes": [
        {"name": "Over", "price": over, "point": point},
        {"name": "Under", "price": under, "point": point},
    ]}


class OddsMathTest(unittest.TestCase):
    def test_conversions_round_trip(self) -> None:
        for american in (-250, -110, 100, 105, 150, 400):
            self.assertEqual(decimal_to_american(american_to_decimal(american)), american)

    def test_arb_return_matches_hand_calculation(self) -> None:
        # 2.05 and 2.03: 1/(1/2.05 + 1/2.03) - 1 = 1.9975%
        self.assertAlmostEqual(arb_return_pct([2.05, 2.03]), 1.9975, places=3)
        self.assertLess(arb_return_pct([1.909, 1.909]), 0)

    def test_balanced_stakes_pay_equally(self) -> None:
        stakes = balanced_stakes([2.05, 2.03], 1000)
        self.assertAlmostEqual(sum(stakes), 1000)
        self.assertAlmostEqual(stakes[0] * 2.05, stakes[1] * 2.03)

    def test_round_stakes_to_whole_dollars(self) -> None:
        self.assertEqual(round_stakes([497.56, 502.44], 1), [498, 502])
        self.assertEqual(round_stakes([1.2], 5), [5])

    def test_guaranteed_profit_is_worst_case(self) -> None:
        self.assertAlmostEqual(guaranteed_profit([100, 100], [2.1, 1.95]), -5.0)


class ScanGameTest(unittest.TestCase):
    def test_detects_two_way_moneyline_arb(self) -> None:
        game = _game([
            _book("dk", [_h2h({"Yankees": 105, "Red Sox": -120})]),
            _book("fd", [_h2h({"Yankees": -125, "Red Sox": 103})]),
        ])
        [arb] = scan_game(game, NOW, OPEN)
        legs = {q.selection: q for q in arb.legs}
        self.assertEqual((legs["Yankees"].book, legs["Yankees"].american), ("dk", 105))
        self.assertEqual((legs["Red Sox"].book, legs["Red Sox"].american), ("fd", 103))
        self.assertAlmostEqual(arb.return_pct, 1.9975, places=3)
        self.assertEqual(arb.book_count, 2)
        self.assertFalse(arb.suspicious)

    def test_no_arb_on_standard_juice(self) -> None:
        game = _game([_book("dk", [_h2h({"Yankees": -110, "Red Sox": -110})])])
        self.assertEqual(scan_game(game, NOW, OPEN), [])

    def test_near_miss_kept_when_threshold_negative(self) -> None:
        game = _game([_book("dk", [_h2h({"Yankees": -102, "Red Sox": -102})])])
        [miss] = scan_game(game, NOW, ScanConfig(min_return_pct=-1.5))
        self.assertLess(miss.return_pct, 0)

    def test_three_way_soccer_arb(self) -> None:
        game = _game([
            _book("dk", [_h2h({"Yankees": 260, "Red Sox": 150, "Draw": 210})]),
            _book("fd", [_h2h({"Yankees": 200, "Red Sox": 200, "Draw": 230})]),
            _book("mgm", [_h2h({"Yankees": 310, "Red Sox": 130, "Draw": 220})]),
        ])
        [arb] = scan_game(game, NOW, OPEN)
        self.assertEqual(len(arb.legs), 3)
        self.assertEqual({q.book for q in arb.legs}, {"mgm", "fd"})
        self.assertGreater(arb.return_pct, 0)

    def test_two_way_and_three_way_books_are_not_mixed(self) -> None:
        # Combining a 2-way price with a 3-way price would leave the draw uncovered.
        game = _game([
            _book("dk", [_h2h({"Yankees": 300, "Red Sox": 300, "Draw": 100})]),
            _book("fd", [_h2h({"Yankees": 150, "Red Sox": 150})]),
        ])
        for arb in scan_game(game, NOW, ScanConfig(min_return_pct=-100)):
            self.assertEqual(len({q.book for q in arb.legs}), 1)

    def test_spread_arb_requires_matching_lines(self) -> None:
        game = _game([
            _book("dk", [_spread(-1.5, 110, 1.5, -130)]),
            _book("fd", [_spread(-1.5, -130, 1.5, 105)]),
            _book("mgm", [_spread(-2.5, 200, 2.5, 200)]),  # different line, ignored... unless it arbs itself
        ])
        arbs = [a for a in scan_game(game, NOW, OPEN) if a.line == -1.5]
        [arb] = arbs
        self.assertEqual(arb.market, "spreads")
        self.assertEqual({(q.book, q.point) for q in arb.legs}, {("dk", -1.5), ("fd", 1.5)})

    def test_totals_arb(self) -> None:
        game = _game([
            _book("dk", [_total(8.5, 108, -130)]),
            _book("fd", [_total(8.5, -130, 104)]),
            _book("mgm", [_total(9.0, 150, 150)]),
        ])
        arbs = [a for a in scan_game(game, NOW, OPEN) if a.line == 8.5]
        [arb] = arbs
        self.assertEqual(payload_outcomes(arb), {"Over 8.5", "Under 8.5"})

    def test_started_games_skipped_unless_live_enabled(self) -> None:
        game = _game([
            _book("dk", [_h2h({"Yankees": 105, "Red Sox": -120})]),
            _book("fd", [_h2h({"Yankees": -125, "Red Sox": 103})]),
        ], commence=PAST)
        self.assertEqual(scan_game(game, NOW, OPEN), [])
        self.assertEqual(len(scan_game(game, NOW, ScanConfig(include_live=True))), 1)

    def test_stale_quotes_dropped(self) -> None:
        game = _game([
            _book("dk", [_h2h({"Yankees": 105, "Red Sox": -120}, updated=STALE)]),
            _book("fd", [_h2h({"Yankees": -125, "Red Sox": 103})]),
        ])
        self.assertEqual(scan_game(game, NOW, ScanConfig(max_quote_age_s=600)), [])
        self.assertEqual(len(scan_game(game, NOW, OPEN)), 1)

    def test_book_filter(self) -> None:
        game = _game([
            _book("dk", [_h2h({"Yankees": 105, "Red Sox": -120})]),
            _book("fd", [_h2h({"Yankees": -125, "Red Sox": 103})]),
        ])
        self.assertEqual(scan_game(game, NOW, ScanConfig(books=frozenset({"dk"}))), [])

    def test_exchange_commission_can_kill_an_arb(self) -> None:
        game = _game([
            _book("dk", [_h2h({"Yankees": 102, "Red Sox": -120})]),
            _book("betfair_ex_uk", [_h2h({"Yankees": -125, "Red Sox": 102})]),
        ])
        self.assertEqual(len(scan_game(game, NOW, ScanConfig(commissions={}))), 1)
        self.assertEqual(scan_game(game, NOW, OPEN), [])

    def test_single_book_arb_flagged_suspicious(self) -> None:
        game = _game([_book("dk", [_h2h({"Yankees": 110, "Red Sox": 110})])])
        [arb] = scan_game(game, NOW, OPEN)
        self.assertTrue(arb.suspicious)

    def test_scan_games_sorts_best_first(self) -> None:
        small = _game([
            _book("dk", [_h2h({"Yankees": 102, "Red Sox": -120})]),
            _book("fd", [_h2h({"Yankees": -125, "Red Sox": 101})]),
        ])
        big = dict(_game([
            _book("dk", [_h2h({"Yankees": 120, "Red Sox": -120})]),
            _book("fd", [_h2h({"Yankees": -125, "Red Sox": 110})]),
        ]), id="g2")
        arbs = scan_games([small, big], OPEN, now=NOW)
        self.assertEqual([a.game_id for a in arbs], ["g2", "g1"])


class PayloadTest(unittest.TestCase):
    def test_rounded_stakes_and_profit(self) -> None:
        game = _game([
            _book("dk", [_h2h({"Yankees": 105, "Red Sox": -120})]),
            _book("fd", [_h2h({"Yankees": -125, "Red Sox": 103})]),
        ])
        [arb] = scan_game(game, NOW, OPEN)
        p = to_payload(arb, bankroll=1000, round_to=1)
        self.assertTrue(all(float(leg["stake"]).is_integer() for leg in p["legs"]))
        self.assertAlmostEqual(p["total_stake"], 1000, delta=1)
        self.assertGreater(p["guaranteed_profit"], 15)
        self.assertEqual(p["profit_pct"], 1.998)


def payload_outcomes(arb) -> set[str]:
    return {leg["outcome"] for leg in to_payload(arb)["legs"]}


if __name__ == "__main__":
    unittest.main()

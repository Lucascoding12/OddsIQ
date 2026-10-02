"""Tests for the arb scanner math."""
import unittest

from services.arb_scanner import find_arb_in_game


def _game(bookmakers: list[dict]) -> dict:
    return {
        "id": "g1",
        "sport_key": "baseball_mlb",
        "home_team": "Yankees",
        "away_team": "Red Sox",
        "commence_time": "2026-06-11T23:00:00Z",
        "bookmakers": bookmakers,
    }


def _book(key: str, outcomes: dict[str, int]) -> dict:
    return {
        "key": key,
        "title": key,
        "markets": [
            {
                "key": "h2h",
                "outcomes": [{"name": n, "price": p} for n, p in outcomes.items()],
            }
        ],
    }


class FindArbTest(unittest.TestCase):
    def test_detects_two_way_arb(self) -> None:
        # Best prices across books: +105 and +103 → 98.05% combined implied
        game = _game([
            _book("dk", {"Yankees": 105, "Red Sox": -120}),
            _book("fd", {"Yankees": -125, "Red Sox": 103}),
        ])

        opp = find_arb_in_game(game)

        self.assertIsNotNone(opp)
        self.assertGreater(opp.profit_pct, 0)
        self.assertEqual(len(opp.legs), 2)
        legs = {leg.outcome: leg for leg in opp.legs}
        self.assertEqual(legs["Yankees"].odds, 105)
        self.assertEqual(legs["Yankees"].book, "dk")
        self.assertEqual(legs["Red Sox"].odds, 103)
        self.assertEqual(legs["Red Sox"].book, "fd")
        # Both legs should pay out roughly the same (that's the point of an arb)
        self.assertAlmostEqual(legs["Yankees"].payout, legs["Red Sox"].payout, delta=0.5)

    def test_no_arb_when_implied_prob_exceeds_one(self) -> None:
        game = _game([_book("dk", {"Yankees": -110, "Red Sox": -110})])
        self.assertIsNone(find_arb_in_game(game))

    def test_skips_three_way_markets(self) -> None:
        game = _game([_book("dk", {"Arsenal": 150, "Chelsea": 200, "Draw": 220})])
        self.assertIsNone(find_arb_in_game(game))

    def test_skips_games_without_bookmakers(self) -> None:
        self.assertIsNone(find_arb_in_game(_game([])))


if __name__ == "__main__":
    unittest.main()

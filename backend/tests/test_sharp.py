"""Tests for the sharp metrics derivations."""
import unittest

from api.v1.sharp import _compute_line_movement, _compute_no_vig


def _game(bookmakers: list[dict]) -> dict:
    return {
        "sport_key": "baseball_mlb",
        "home_team": "Yankees",
        "away_team": "Red Sox",
        "commence_time": "2026-06-11T23:00:00Z",
        "bookmakers": bookmakers,
    }


def _book(title: str, outcomes: dict[str, int]) -> dict:
    return {
        "key": title.lower(),
        "title": title,
        "markets": [
            {
                "key": "h2h",
                "outcomes": [{"name": n, "price": p} for n, p in outcomes.items()],
            }
        ],
    }


class LineMovementTest(unittest.TestCase):
    def test_flags_large_book_disagreement_as_steam(self) -> None:
        # -150 implies 60%, +120 implies ~45.5% → ~14.5 pt gap on the same side
        games = [_game([
            _book("LagBook", {"Yankees": -150, "Red Sox": 130}),
            _book("SharpBook", {"Yankees": 120, "Red Sox": -140}),
        ])]

        results = _compute_line_movement(games)

        self.assertTrue(results)
        yankees = next(r for r in results if r["outcome"] == "Yankees")
        self.assertTrue(yankees["steamFlag"])
        self.assertEqual(yankees["bestOdds"], 120)
        self.assertEqual(yankees["bestBook"], "SharpBook")
        self.assertEqual(yankees["worstOdds"], -150)
        self.assertEqual(yankees["worstBook"], "LagBook")

    def test_ignores_agreeing_books(self) -> None:
        games = [_game([
            _book("A", {"Yankees": -110, "Red Sox": -110}),
            _book("B", {"Yankees": -112, "Red Sox": -108}),
        ])]
        self.assertEqual(_compute_line_movement(games), [])


class NoVigTest(unittest.TestCase):
    def test_fair_probs_sum_to_100(self) -> None:
        games = [_game([_book("A", {"Yankees": -120, "Red Sox": 100})])]

        results = _compute_no_vig(games)

        self.assertEqual(len(results), 1)
        entry = results[0]
        self.assertAlmostEqual(
            entry["consensusFairHomeProb"] + entry["consensusFairAwayProb"], 100, delta=0.05
        )
        self.assertGreater(entry["avgVigPct"], 0)


if __name__ == "__main__":
    unittest.main()

"""Tests for the /odds normalization logic."""
import unittest

from api.v1.odds import _normalize_game


def _book(key: str, title: str, home: tuple[str, int], away: tuple[str, int]) -> dict:
    return {
        "key": key,
        "title": title,
        "markets": [
            {
                "key": "h2h",
                "outcomes": [
                    {"name": home[0], "price": home[1]},
                    {"name": away[0], "price": away[1]},
                ],
            }
        ],
    }


class NormalizeGameTest(unittest.TestCase):
    def test_picks_best_price_per_side_independently(self) -> None:
        game = {
            "id": "g1",
            "sport_key": "baseball_mlb",
            "home_team": "Yankees",
            "away_team": "Red Sox",
            "commence_time": "2026-06-11T23:00:00Z",
            "bookmakers": [
                _book("dk", "DraftKings", ("Yankees", -120), ("Red Sox", 110)),
                _book("fd", "FanDuel", ("Yankees", -110), ("Red Sox", 100)),
            ],
        }

        normalized = _normalize_game(game)

        self.assertEqual(normalized["bestLine"]["homeMoneyline"], -110)
        self.assertEqual(normalized["bestLine"]["awayMoneyline"], 110)
        # DraftKings has the lower combined implied probability (less vig)
        self.assertEqual(normalized["bestLine"]["book"], "DraftKings")
        self.assertEqual(normalized["sport"], "MLB")
        self.assertEqual(normalized["category"], "Baseball")

    def test_unknown_sport_key_falls_back_gracefully(self) -> None:
        game = {
            "id": "g2",
            "sport_key": "underwater_basket_weaving",
            "home_team": "A",
            "away_team": "B",
            "commence_time": "",
            "bookmakers": [],
        }

        normalized = _normalize_game(game)

        self.assertEqual(normalized["sport"], "underwater_basket_weaving")
        self.assertEqual(normalized["category"], "Other")
        self.assertIsNone(normalized["bestLine"]["homeMoneyline"])
        self.assertIsNone(normalized["bestLine"]["awayMoneyline"])


if __name__ == "__main__":
    unittest.main()

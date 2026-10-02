"""Tests for de-vig math and the +EV engine."""
import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from services.ev_engine import ev_from_grouped, fair_line
from services.markets import ScanConfig, group_game
from services.odds_math import american_to_decimal, devig_power, kelly_fraction
from services.odds_store import store

NOW = datetime.fromisoformat("2026-10-02T12:00:00+00:00").timestamp()


def _game(books: dict[str, tuple[int, int]]) -> dict:
    return {
        "id": "g1",
        "sport_key": "americanfootball_nfl",
        "sport_title": "NFL",
        "home_team": "Chiefs",
        "away_team": "Bills",
        "commence_time": "2099-01-01T00:00:00Z",
        "bookmakers": [
            {"key": k, "title": k.title(), "markets": [{"key": "h2h", "outcomes": [
                {"name": "Chiefs", "price": home}, {"name": "Bills", "price": away},
            ]}]}
            for k, (home, away) in books.items()
        ],
    }


def _grouped(books: dict[str, tuple[int, int]]):
    return group_game(_game(books), NOW, ScanConfig())


class DevigTest(unittest.TestCase):
    def test_symmetric_market_devigs_to_even(self) -> None:
        d = american_to_decimal(-110)
        self.assertEqual([round(p, 6) for p in devig_power([d, d])], [0.5, 0.5])

    def test_probabilities_sum_to_one(self) -> None:
        probs = devig_power([american_to_decimal(-300), american_to_decimal(240)])
        self.assertAlmostEqual(sum(probs), 1.0, places=9)

    def test_power_shades_longshot_more_than_proportional(self) -> None:
        fav, dog = american_to_decimal(-400), american_to_decimal(300)
        proportional_dog = (1 / dog) / (1 / fav + 1 / dog)
        self.assertLess(devig_power([fav, dog])[1], proportional_dog)

    def test_kelly(self) -> None:
        self.assertAlmostEqual(kelly_fraction(0.55, 2.0), 0.10)
        self.assertEqual(kelly_fraction(0.40, 2.0), 0.0)


class EvEngineTest(unittest.TestCase):
    def test_no_sharp_book_means_no_fair_line(self) -> None:
        gm = _grouped({"draftkings": (-110, -110), "fanduel": (-105, -115)})
        self.assertIsNone(fair_line(gm, next(iter(gm.groups))))

    def test_soft_price_above_fair_is_positive_ev(self) -> None:
        # Pinnacle says a coin flip; FanDuel pays +115 on the Bills.
        gm = _grouped({"pinnacle": (-105, -105), "fanduel": (-135, 115)})
        [bet] = ev_from_grouped(gm, ScanConfig())
        self.assertEqual(bet.selection, "Bills")
        self.assertEqual(bet.offers[0][0].book, "fanduel")
        self.assertAlmostEqual(bet.fair_prob, 0.5, places=6)
        self.assertAlmostEqual(bet.ev_pct, 7.5, places=6)
        self.assertEqual(bet.sharp_books, ("Pinnacle",))

    def test_sharp_books_are_never_targets(self) -> None:
        gm = _grouped({"pinnacle": (-105, -105), "novig": (102, 102)})
        self.assertEqual(ev_from_grouped(gm, ScanConfig()), [])

    def test_lowvig_not_double_counted_with_betonline(self) -> None:
        gm = _grouped({"betonlineag": (-110, -110), "lowvig": (-150, 130), "fanduel": (120, -140)})
        _, titles = fair_line(gm, next(iter(gm.groups)))
        self.assertEqual(titles, ("Betonlineag",))

    def test_sharps_are_blended_by_weight(self) -> None:
        gm = _grouped({"pinnacle": (-110, -110), "novig": (-150, 150)})
        probs, _ = fair_line(gm, next(iter(gm.groups)))
        self.assertGreater(probs["Chiefs"], 0.5)
        self.assertLess(probs["Chiefs"], 0.6)  # Pinnacle (weight 1.0) pulls it toward 50%

    def test_offers_ranked_best_first(self) -> None:
        gm = _grouped({"pinnacle": (-105, -105), "fanduel": (-135, 115), "draftkings": (-130, 108)})
        [bet] = ev_from_grouped(gm, ScanConfig())
        self.assertEqual([q.book for q, _ in bet.offers], ["fanduel", "draftkings"])


class EvApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from main import app
        cls.client = TestClient(app)

    def setUp(self) -> None:
        store.update([_game({"pinnacle": (-105, -105), "fanduel": (-135, 115), "draftkings": (-130, 108)})])

    def test_ev_endpoint_with_kelly_stake(self) -> None:
        [bet] = self.client.get("/api/v1/ev?bankroll=1000&kelly=0.25&round_to=0").json()
        self.assertEqual(bet["book"], "fanduel")
        self.assertEqual(bet["pick"], "Bills")
        # full Kelly = 0.075 / 1.15 → quarter of that on $1000
        self.assertAlmostEqual(bet["stake"], 1000 * 0.25 * 0.075 / 1.15, places=1)
        self.assertEqual(bet["also"][0]["book"], "draftkings")

    def test_book_filter_falls_back_to_next_best_book(self) -> None:
        [bet] = self.client.get("/api/v1/ev?books=draftkings").json()
        self.assertEqual(bet["book"], "draftkings")
        self.assertEqual(bet["also"], [])

    def test_min_edge_filters(self) -> None:
        self.assertEqual(self.client.get("/api/v1/ev?min_ev_pct=10").json(), [])

    def test_ev_page_renders(self) -> None:
        self.assertIn("Kelly fraction", self.client.get("/ev").text)
        self.assertNotIn('value="pinnacle"', self.client.get("/ev").text)


if __name__ == "__main__":
    unittest.main()

"""Tests for calculators, line shopping, sharp metrics and the pages that show them."""
import unittest

from fastapi.testclient import TestClient

from services import calculators, line_shop, sharp_metrics
from services.markets import ScanConfig, group_game
from services.odds_store import store

NOW = 0.0


def _book(key: str, h2h: tuple[int, int], spread: tuple[float, int, int] | None = None) -> dict:
    markets = [{"key": "h2h", "outcomes": [{"name": "Chiefs", "price": h2h[0]}, {"name": "Bills", "price": h2h[1]}]}]
    if spread:
        pt, home_px, away_px = spread
        markets.append({"key": "spreads", "outcomes": [
            {"name": "Chiefs", "price": home_px, "point": pt},
            {"name": "Bills", "price": away_px, "point": -pt},
        ]})
    return {"key": key, "title": key.title(), "markets": markets}


def _game(books: list[dict], gid: str = "g1") -> dict:
    return {"id": gid, "sport_key": "americanfootball_nfl", "sport_title": "NFL",
            "home_team": "Kansas City Chiefs", "away_team": "Buffalo Bills",
            "commence_time": "2099-01-01T00:00:00Z", "bookmakers": books}


def _grouped(books: list[dict]):
    game = _game(books)
    # Team names in _book are short; align them with the game's full names.
    for b in game["bookmakers"]:
        for m in b["markets"]:
            for o in m["outcomes"]:
                o["name"] = {"Chiefs": "Kansas City Chiefs", "Bills": "Buffalo Bills"}[o["name"]]
    return [group_game(game, NOW, ScanConfig())], game


class CalculatorsTest(unittest.TestCase):
    def test_every_calculator_runs_on_its_defaults(self) -> None:
        for calc in calculators.CALCULATORS:
            result, error = calculators.run(calc, {})
            self.assertIsNone(error, calc.slug)
            self.assertTrue(result.metrics, calc.slug)

    def test_arbitrage_uses_return_on_stake(self) -> None:
        result, _ = calculators.run(calculators.BY_SLUG["arbitrage"], {"odds": "+105, +103", "round_to": "0"})
        self.assertEqual(dict((l, v) for l, v, _ in result.metrics)["Return"], "2.00%")

    def test_point_spread_favorite_above_half(self) -> None:
        result, _ = calculators.run(calculators.BY_SLUG["point-spread"], {"spread": "-3.5", "sport": "nfl"})
        self.assertEqual(result.metrics[0][1], "60.27%")

    def test_converter_accepts_every_format(self) -> None:
        conv = calculators.BY_SLUG["converter"]
        for raw in ("+105", "2.05", "21/20"):
            result, error = calculators.run(conv, {"value": raw})
            self.assertIsNone(error, raw)
            self.assertEqual(result.metrics[0][1], "+105", raw)

    def test_bonus_bet_warns_when_prices_cannot_be_opposite_sides(self) -> None:
        result, _ = calculators.run(calculators.BY_SLUG["bonus-bet"], {"bonus_odds": "+400", "hedge_odds": "-150"})
        self.assertTrue(result.notes)
        result, _ = calculators.run(calculators.BY_SLUG["bonus-bet"], {})
        self.assertEqual(result.notes, [])

    def test_bad_input_returns_message(self) -> None:
        _, error = calculators.run(calculators.BY_SLUG["implied"], {"odds": "50"})
        self.assertIn("American odds", error)


class LineShopTest(unittest.TestCase):
    def test_parse_bet_style_query(self) -> None:
        pq = line_shop.parse("chiefs -3.5")
        self.assertEqual((pq.words, pq.points), (("chiefs",), (3.5,)))
        pq = line_shop.parse("o47.5 bills")
        self.assertEqual((pq.market, pq.side_word, pq.points), ("totals", "over", (47.5,)))
        self.assertEqual(line_shop.parse("yankees ml").market, "h2h")

    def test_search_ranks_books_and_focuses_team(self) -> None:
        grouped, _ = _grouped([
            _book("draftkings", (-150, 130), (-3.5, -110, -110)),
            _book("fanduel", (-145, 125), (-3.5, -105, -115)),
            _book("pinnacle", (-148, 135), (-3.5, -108, -102)),
        ])
        [game] = line_shop.search(grouped, "chiefs -3.5")
        [block] = game["blocks"]
        [side] = block["sides"]
        self.assertEqual(block["market"], "Spread")
        self.assertEqual(side["pick"], "Kansas City Chiefs -3.5")
        self.assertEqual(side["best"]["book_title"], "Fanduel")
        self.assertEqual([r["odds"] for r in side["rows"]], [-105, -108, -110])
        self.assertIsNotNone(side["rows"][0]["ev_pct"])

    def test_no_match(self) -> None:
        grouped, _ = _grouped([_book("draftkings", (-150, 130))])
        self.assertEqual(line_shop.search(grouped, "lakers"), [])


class SharpMetricsTest(unittest.TestCase):
    def test_sharp_vs_public_finds_sharp_side(self) -> None:
        grouped, _ = _grouped([
            _book("pinnacle", (-180, 160)),
            _book("draftkings", (-140, 120)),
            _book("fanduel", (-140, 118)),
            _book("betmgm", (-145, 122)),
        ])
        [row] = sharp_metrics.sharp_vs_public(grouped)
        self.assertEqual(row["pick"], "Kansas City Chiefs")
        self.assertGreater(row["gap_pts"], 3)

    def test_book_holds_rank_low_margin_first(self) -> None:
        grouped, _ = _grouped([_book("pinnacle", (-105, -105)), _book("draftkings", (-115, -115))])
        grouped = grouped * 5  # holds need at least 5 markets per book
        holds = sharp_metrics.book_holds(grouped)
        self.assertEqual([h["book"] for h in holds], ["pinnacle", "draftkings"])

    def test_tracker_flags_steam_and_lagging_books(self) -> None:
        tracker = sharp_metrics.MoveTracker()
        before, _ = _grouped([_book("pinnacle", (-110, -110)), _book("novig", (-110, -110)), _book("draftkings", (-110, -110))])
        tracker.observe(before, "2026-10-02T12:00:00+00:00")
        after, _ = _grouped([_book("pinnacle", (-150, 130)), _book("novig", (-150, 130)), _book("draftkings", (-110, -110))])
        tracker.observe(after, "2026-10-02T12:05:00+00:00")
        moves = tracker.moves(after)
        chiefs = next(m for m in moves if m["pick"] == "Kansas City Chiefs")
        self.assertTrue(chiefs["steam"])
        self.assertEqual(chiefs["direction"], "toward")
        self.assertEqual([l["book_title"] for l in chiefs["lagging"]], ["Draftkings"])


class PagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from main import app
        cls.client = TestClient(app)

    def setUp(self) -> None:
        _, game = _grouped([_book("pinnacle", (-150, 130), (-3.5, -108, -102)),
                            _book("draftkings", (-140, 125), (-3.5, -110, -110))])
        store.update([game])

    def test_pages_render(self) -> None:
        for path in ("/", "/ev", "/shop", "/sharp", "/calc", "/calc?c=poisson"):
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_calc_fragment(self) -> None:
        html = self.client.get("/ui/calc/implied?odds=-150").text
        self.assertIn("60.00%", html)

    def test_json_tools(self) -> None:
        self.assertEqual(self.client.get("/api/v1/shop?q=chiefs").status_code, 200)
        self.assertIn("holds", self.client.get("/api/v1/sharp/summary").json())
        body = self.client.post("/api/v1/calc/parlay", json={"odds": "-110,-110", "stake": "10"}).json()
        self.assertEqual(body["metrics"][0][1], "+264")


if __name__ == "__main__":
    unittest.main()

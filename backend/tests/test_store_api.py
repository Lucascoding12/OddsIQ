"""Tests for the in-memory store and the arb HTTP endpoints."""
import unittest

from fastapi.testclient import TestClient

from services.odds_store import store


def _arb_game(game_id: str = "g1", yankees: int = 105) -> dict:
    def book(key: str, prices: dict[str, int]) -> dict:
        return {"key": key, "title": key.upper(), "markets": [
            {"key": "h2h", "outcomes": [{"name": n, "price": p} for n, p in prices.items()]},
        ]}
    return {
        "id": game_id,
        "sport_key": "baseball_mlb",
        "sport_title": "MLB",
        "home_team": "Yankees",
        "away_team": "Red Sox",
        "commence_time": "2099-01-01T00:00:00Z",
        "bookmakers": [
            book("dk", {"Yankees": yankees, "Red Sox": -120}),
            book("fd", {"Yankees": -125, "Red Sox": 103}),
        ],
    }


class StoreTest(unittest.TestCase):
    def test_update_scans_and_bumps_version(self) -> None:
        before = store.version
        store.update([_arb_game()])
        self.assertEqual(store.version, before + 1)
        self.assertEqual(len([a for a in store.arbs if a.return_pct > 0]), 1)

    def test_first_seen_survives_price_change_and_clears_when_gone(self) -> None:
        store.update([_arb_game(yankees=105)])
        arb_id = store.arbs[0].id
        seen = store.first_seen[arb_id]
        store.update([_arb_game(yankees=110)])
        self.assertEqual(store.first_seen[arb_id], seen)
        store.update([])
        self.assertNotIn(arb_id, store.first_seen)

    def test_memo_recomputes_only_on_new_version(self) -> None:
        store.update([])
        calls = []
        store.memo("k", lambda: calls.append(1))
        store.memo("k", lambda: calls.append(1))
        self.assertEqual(len(calls), 1)
        store.update([])
        store.memo("k", lambda: calls.append(1))
        self.assertEqual(len(calls), 2)


class ArbApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from main import app
        # No context manager: skips lifespan, so no Redis or Odds API calls.
        cls.client = TestClient(app)

    def setUp(self) -> None:
        store.update([_arb_game()])

    def test_opportunities_backwards_compatible_shape(self) -> None:
        [opp] = self.client.get("/api/v1/arb/opportunities").json()
        for key in ("game_id", "sport_key", "home_team", "away_team", "commence_time",
                    "legs", "profit_pct", "total_stake"):
            self.assertIn(key, opp)
        self.assertEqual({leg["book"] for leg in opp["legs"]}, {"dk", "fd"})
        self.assertAlmostEqual(opp["total_stake"], 100, delta=0.02)

    def test_bankroll_and_rounding(self) -> None:
        [opp] = self.client.get("/api/v1/arb/opportunities?bankroll=500&round_to=5").json()
        self.assertTrue(all(leg["stake"] % 5 == 0 for leg in opp["legs"]))

    def test_book_filter_rescans(self) -> None:
        self.assertEqual(self.client.get("/api/v1/arb/opportunities?books=dk").json(), [])

    def test_calc(self) -> None:
        body = self.client.post("/api/v1/arb/calc", json={"odds": [105, 103], "bankroll": 1000}).json()
        self.assertTrue(body["is_arb"])
        self.assertAlmostEqual(body["profit_pct"], 1.998, places=3)

    def test_calc_rejects_invalid_american_odds(self) -> None:
        self.assertEqual(self.client.post("/api/v1/arb/calc", json={"odds": [50, 103]}).status_code, 422)

    def test_status(self) -> None:
        body = self.client.get("/api/v1/status").json()
        self.assertEqual(body["arbs"], 1)


class AdminPollTest(unittest.TestCase):
    def test_remote_poll_rejected_without_token(self) -> None:
        from main import app
        # TestClient's client host is "testclient", i.e. not local.
        self.assertEqual(TestClient(app).post("/api/v1/admin/poll").status_code, 403)

    def test_wrong_token_rejected(self) -> None:
        from unittest.mock import patch
        from main import app, settings
        with patch.object(settings, "admin_token", "s3cret"):
            r = TestClient(app).post("/api/v1/admin/poll", headers={"X-Admin-Token": "nope"})
        self.assertEqual(r.status_code, 403)


class UiTest(unittest.TestCase):
    def setUp(self) -> None:
        store.update([_arb_game()])

    def test_index_page_lists_books(self) -> None:
        from main import app
        html = TestClient(app).get("/").text
        self.assertIn('value="dk"', html)
        self.assertIn("EventSource", html)

    def test_board_renders_stakes_and_escapes_names(self) -> None:
        from api.v1.arb import ArbQuery
        from ui.routes import render_arbs
        game = _arb_game()
        game["home_team"] = "<script>x</script>"
        game["bookmakers"][0]["markets"][0]["outcomes"][0]["name"] = "<script>x</script>"
        game["bookmakers"][1]["markets"][0]["outcomes"][0]["name"] = "<script>x</script>"
        store.update([game])
        q = ArbQuery(None, None, 0.0, None, 100.0, 1.0, False, False)
        html = render_arbs(q)
        self.assertIn("Bet $", html)
        self.assertIn("2 books quoting", html)
        self.assertNotIn("<script>x", html)


if __name__ == "__main__":
    unittest.main()

"""Tests for the Kelly math and the claims the Kelly page makes."""
import unittest

from fastapi.testclient import TestClient

from services import kelly
from services.odds_math import kelly_fraction


class KellyMathTest(unittest.TestCase):
    P, D = 0.55, 2.10

    def test_growth_peaks_at_full_kelly(self) -> None:
        full = kelly_fraction(self.P, self.D)
        peak = kelly.growth_rate(full, self.P, self.D)
        for f in (full * 0.9, full * 1.1):
            self.assertLess(kelly.growth_rate(f, self.P, self.D), peak)

    def test_half_kelly_keeps_about_three_quarters_of_growth(self) -> None:
        full = kelly_fraction(self.P, self.D)
        ratio = kelly.growth_rate(full / 2, self.P, self.D) / kelly.growth_rate(full, self.P, self.D)
        self.assertAlmostEqual(ratio, 0.75, delta=0.03)

    def test_growth_turns_negative_past_twice_kelly(self) -> None:
        full = kelly_fraction(self.P, self.D)
        self.assertLess(kelly.growth_rate(full * 2.2, self.P, self.D), 0)

    def test_drawdown_chances_match_thorp(self) -> None:
        self.assertAlmostEqual(kelly.drawdown_chance(1.0), 0.5)
        self.assertAlmostEqual(kelly.drawdown_chance(0.5), 0.125)
        self.assertEqual(kelly.drawdown_chance(2.0), 1.0)

    def test_no_edge_no_curve(self) -> None:
        self.assertEqual(kelly.growth_curve(0.45, 2.0), [])

    def test_sheet_scales_to_exposure_cap(self) -> None:
        bets = [{"label": f"b{i}", "book_title": "X", "odds": 110, "decimal": 2.10, "fair_prob": 0.55,
                 "fair_prob_low": 0.53, "ev_pct": 15.5, "confidence": "strong"} for i in range(10)]
        rows, scale = kelly.kelly_sheet(bets, 1000, 1.0, 0.25, 0, conservative=False)
        self.assertLess(scale, 1)
        self.assertAlmostEqual(sum(r.stake for r in rows), 250, delta=0.1)

    def test_conservative_uses_lower_probability(self) -> None:
        bet = [{"label": "b", "book_title": "X", "odds": 110, "decimal": 2.10, "fair_prob": 0.55,
                "fair_prob_low": 0.50, "ev_pct": 15.5, "confidence": "fair"}]
        normal, _ = kelly.kelly_sheet(bet, 1000, 0.25, 1, 0, conservative=False)
        careful, _ = kelly.kelly_sheet(bet, 1000, 0.25, 1, 0, conservative=True)
        self.assertLess(careful[0].stake, normal[0].stake)


class KellyPageTest(unittest.TestCase):
    def test_page_and_board_render(self) -> None:
        from main import app
        from ui.routes import _render_kelly
        self.assertEqual(TestClient(app).get("/kelly").status_code, 200)
        html = _render_kelly(1000, "+110", 55, "", 0.25, 25, 1, False)
        self.assertIn("Quarter Kelly", html)
        self.assertIn("<svg", html)
        self.assertIn("No edge", _render_kelly(1000, "-110", 50, "", 0.25, 25, 1, False))


if __name__ == "__main__":
    unittest.main()

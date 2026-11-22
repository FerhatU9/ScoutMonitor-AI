"""API tests for safe, read-only fictional player browsing and comparison."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app


class TestDemoCatalog(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_list_has_twenty_players_and_source_label(self):
        response = self.client.get("/api/v1/demo/players")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 20)
        self.assertEqual(len(data["players"]), 20)
        self.assertEqual(data["data_source"], "synthetic_v1")
        self.assertTrue(all(p["is_synthetic"] for p in data["players"]))

    def test_filter_league_and_minutes(self):
        response = self.client.get(
            "/api/v1/demo/players", params={"league": "imaginary league a", "min_minutes": 1500}
        )
        self.assertEqual(response.status_code, 200)
        players = response.json()["players"]
        self.assertTrue(players)
        self.assertTrue(all(p["league"] == "Imaginary League A" for p in players))
        self.assertTrue(all(p["minutes"] >= 1500 for p in players))

    def test_foot_filter(self):
        response = self.client.get("/api/v1/demo/players?preferred_foot=left")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["players"])
        self.assertTrue(all(p["preferred_foot"] == "left" for p in response.json()["players"]))

    def test_pagination_is_deterministic(self):
        first = self.client.get("/api/v1/demo/players?limit=2&offset=0").json()
        next_page = self.client.get("/api/v1/demo/players?limit=2&offset=2").json()
        self.assertEqual(first["total"], next_page["total"])
        self.assertEqual([p["player_id"] for p in first["players"]], ["SYN001", "SYN002"])
        self.assertEqual([p["player_id"] for p in next_page["players"]], ["SYN003", "SYN004"])

    def test_sorted_metrics_keep_unknown_last(self):
        response = self.client.get(
            "/api/v1/demo/players", params={"sort_by": "progressive_passes_per90", "order": "desc"}
        )
        players = response.json()["players"]
        self.assertEqual(players[0]["player_id"], "SYN020")
        self.assertEqual(players[-1]["player_id"], "SYN006")
        self.assertIsNone(players[-1]["progressive_passes_per90"])

    def test_player_detail_preserves_unknown(self):
        response = self.client.get("/api/v1/demo/players/SYN013")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["defensive_duel_win_pct"])

    def test_player_missing_returns_404(self):
        self.assertEqual(self.client.get("/api/v1/demo/players/NOT_REAL").status_code, 404)

    def test_comparison_returns_signed_differences(self):
        response = self.client.get("/api/v1/demo/compare?first_id=SYN001&second_id=SYN002")
        self.assertEqual(response.status_code, 200)
        diff = response.json()["difference_second_minus_first"]
        self.assertEqual(diff["minutes"], 105)
        self.assertAlmostEqual(diff["progressive_passes_per90"], 0.17)
        self.assertAlmostEqual(diff["defensive_duel_win_pct"], 1.1)

    def test_comparison_unknown_metric_is_null(self):
        response = self.client.get("/api/v1/demo/compare?first_id=SYN006&second_id=SYN007")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["difference_second_minus_first"]["progressive_passes_per90"])

    def test_duplicate_comparison_rejected(self):
        response = self.client.get("/api/v1/demo/compare?first_id=SYN001&second_id=SYN001")
        self.assertEqual(response.status_code, 400)

    def test_bad_pagination_and_sort_rejected(self):
        for query in ["limit=0", "limit=101", "offset=-1", "sort_by=private_data", "min_minutes=-2"]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get("/api/v1/demo/players?" + query).status_code, 422)

    def test_invalid_csv_returns_503_without_contents(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text("not,a,valid,csv\nsecret\n", encoding="utf-8")
            with patch("api.main.DEMO_DATA", path):
                response = self.client.get("/api/v1/demo/players")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("secret", response.text)


if __name__ == "__main__":
    unittest.main()

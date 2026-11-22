"""Run with: python -m unittest discover -s tests -v"""

import csv
import tempfile
import unittest
from pathlib import Path

from scoutmonitor.validation import DataValidationError, validate_players


class TestPlayerValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "players.csv"
        with Path("data/fictional_players.csv").open(newline="", encoding="utf-8") as source:
            self.rows = list(csv.DictReader(source))
            self.fields = list(self.rows[0])

    def write_rows(self, rows):
        with self.path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_20_synthetic_players_pass(self):
        self.write_rows(self.rows)
        self.assertEqual(validate_players(self.path), {"players": 20, "rows_with_missing_metrics": 2})

    def test_duplicate_id_fails(self):
        self.rows[1]["player_id"] = self.rows[0]["player_id"]
        self.write_rows(self.rows)
        with self.assertRaises(DataValidationError):
            validate_players(self.path)

    def test_impossible_defensive_percentage_fails(self):
        self.rows[0]["defensive_duel_win_pct"] = "130"
        self.write_rows(self.rows)
        with self.assertRaises(DataValidationError):
            validate_players(self.path)

    def test_unlabelled_real_data_fails(self):
        self.rows[0]["is_synthetic"] = "false"
        self.write_rows(self.rows)
        with self.assertRaises(DataValidationError):
            validate_players(self.path)

    def test_missing_metric_is_not_invented(self):
        self.rows[0]["progressive_passes_per90"] = ""
        self.write_rows(self.rows)
        result = validate_players(self.path)
        self.assertEqual(result["rows_with_missing_metrics"], 3)

    def test_empty_dataset_fails(self):
        self.write_rows([])
        with self.assertRaises(DataValidationError):
            validate_players(self.path)


if __name__ == "__main__":
    unittest.main()

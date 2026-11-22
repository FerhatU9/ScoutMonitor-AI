"""Additional failure-case coverage for the synthetic player-data validator."""

import csv
import tempfile
import unittest
from pathlib import Path

from scoutmonitor.validation import DataValidationError, validate_players


class TestValidationEdges(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.csv_path = Path(self.temporary_directory.name) / "players.csv"
        with Path("data/fictional_players.csv").open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            self.fieldnames = list(reader.fieldnames)
            self.rows = list(reader)

    def save(self, fieldnames=None, rows=None):
        with self.csv_path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=fieldnames or self.fieldnames)
            writer.writeheader()
            writer.writerows(self.rows if rows is None else rows)

    def test_missing_required_column_rejected(self):
        columns = [name for name in self.fieldnames if name != "player_id"]
        self.save(fieldnames=columns, rows=[{k: row[k] for k in columns} for row in self.rows])
        with self.assertRaisesRegex(DataValidationError, "Missing columns"):
            validate_players(self.csv_path)

    def test_invalid_foot_rejected(self):
        self.rows[0]["preferred_foot"] = "unknown"
        self.save()
        with self.assertRaisesRegex(DataValidationError, "invalid preferred foot"):
            validate_players(self.csv_path)

    def test_invalid_age_rejected(self):
        self.rows[0]["age"] = "12"
        self.save()
        with self.assertRaisesRegex(DataValidationError, "invalid numeric field"):
            validate_players(self.csv_path)

    def test_invalid_metric_rejected(self):
        self.rows[0]["progressive_passes_per90"] = "not a number"
        self.save()
        with self.assertRaisesRegex(DataValidationError, "invalid numeric field"):
            validate_players(self.csv_path)

    def test_extra_csv_field_rejected(self):
        self.save()
        with self.csv_path.open("a", encoding="utf-8") as output:
            output.write(",".join(str(self.rows[0][key]) for key in self.fieldnames) + ",extra\n")
        with self.assertRaisesRegex(DataValidationError, "too many CSV values"):
            validate_players(self.csv_path)


if __name__ == "__main__":
    unittest.main()

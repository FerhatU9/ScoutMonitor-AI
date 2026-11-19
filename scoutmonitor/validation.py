"""Validate fictional football player CSV records before using them in an AI workflow."""

import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = {
    "player_id", "player_name", "age", "position", "preferred_foot",
    "league", "minutes", "progressive_passes_per90",
    "defensive_duel_win_pct", "is_synthetic", "source",
}


class DataValidationError(ValueError):
    """Raised when the input data is unsafe or inconsistent."""


def validate_players(csv_path: str | Path) -> dict[str, int]:
    """Validate a *fictional* player CSV; return counts only if every row passes."""
    path = Path(csv_path)
    if not path.is_file():
        raise DataValidationError(f"File does not exist: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise DataValidationError("CSV is missing a header row")
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise DataValidationError("Missing columns: " + ", ".join(sorted(missing)))

        seen_ids: set[str] = set()
        number_of_players = 0
        missing_metric_rows = 0

        for line_no, row in enumerate(reader, start=2):
            if None in row:  # extra unlabelled values in a row
                raise DataValidationError(f"Line {line_no}: too many CSV values")
            player_id = row["player_id"].strip()
            if not player_id or player_id in seen_ids:
                raise DataValidationError(f"Line {line_no}: empty or duplicate player_id")
            seen_ids.add(player_id)

            if not row["player_name"].strip() or not row["league"].strip():
                raise DataValidationError(f"Line {line_no}: name and league are required")
            if row["position"].strip() != "CB":
                raise DataValidationError(f"Line {line_no}: expected centre-back (CB)")
            if row["preferred_foot"].strip().lower() not in {"left", "right", "both"}:
                raise DataValidationError(f"Line {line_no}: invalid preferred foot")
            if row["is_synthetic"].strip().lower() != "true" or row["source"].strip() != "synthetic_v1":
                raise DataValidationError(f"Line {line_no}: data must be labelled synthetic_v1")

            try:
                age = int(row["age"])
                minutes = int(row["minutes"])
                if not 16 <= age <= 50 or not 0 <= minutes <= 6000:
                    raise ValueError("age or minutes outside accepted range")

                missing_metric = False
                for key, limit in (("progressive_passes_per90", 30), ("defensive_duel_win_pct", 100)):
                    value = row[key].strip()
                    if value == "":
                        missing_metric = True
                        continue  # unknown stays unknown; never fill in a value
                    number = float(value)
                    if not 0 <= number <= limit or number != number:
                        raise ValueError(f"{key} outside accepted range")
                missing_metric_rows += int(missing_metric)
            except (ValueError, TypeError, AttributeError) as exc:
                raise DataValidationError(f"Line {line_no}: invalid numeric field ({exc})") from exc

            number_of_players += 1

    if not number_of_players:
        raise DataValidationError("CSV contains no player records")
    return {"players": number_of_players, "rows_with_missing_metrics": missing_metric_rows}


def main() -> int:
    filename = sys.argv[1] if len(sys.argv) > 1 else "data/fictional_players.csv"
    try:
        result = validate_players(filename)
    except (DataValidationError, OSError) as error:
        print(f"FAILED: {error}")
        return 1
    print(f"VALID: {result['players']} fictional players")
    print(f"Rows with unknown metrics: {result['rows_with_missing_metrics']}")
    print("Data source: synthetic_v1 (not real football data)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate reproducible fictional data for engineering exercises only."""

import csv
from pathlib import Path

FIELDS = [
    "player_id", "player_name", "age", "position", "preferred_foot",
    "league", "minutes", "progressive_passes_per90",
    "defensive_duel_win_pct", "is_synthetic", "source",
]


def main() -> None:
    output = Path("data/fictional_players.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for number in range(1, 21):
            writer.writerow({
                "player_id": f"SYN{number:03d}",
                "player_name": f"Fictional Defender {number:02d}",
                "age": 18 + (number % 10),
                "position": "CB",
                "preferred_foot": "left" if number % 3 == 0 else "right",
                "league": "Imaginary League A" if number % 2 == 0 else "Imaginary League B",
                "minutes": 650 + number * 105,
                # Two intentional unknown values to test missing-data handling.
                "progressive_passes_per90": "" if number == 6 else f"{1.0 + number * 0.17:.2f}",
                "defensive_duel_win_pct": "" if number == 13 else f"{50.0 + number * 1.1:.1f}",
                "is_synthetic": "true",
                "source": "synthetic_v1",
            })
    print(f"CREATED: {output} (20 fictional players)")


if __name__ == "__main__":
    main()

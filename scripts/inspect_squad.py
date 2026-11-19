
import json
from pathlib import Path

# Locate the saved football data
project_folder = Path(__file__).resolve().parent.parent
file_path = project_folder / "data" / "fc_copenhagen_squad.json"

# Read the JSON file
with file_path.open("r", encoding="utf-8") as file:
    squad = json.load(file)

# Check how many squad entries we have
print("Total squad entries:", len(squad))

# Check for missing player names
missing_names = 0

for entry in squad:
    player = entry.get("player") or {}
    name = player.get("display_name") or player.get("name")

    if not name:
        missing_names += 1

print("Entries missing player names:", missing_names)

# Check for duplicate player IDs
player_ids = [
    entry["player_id"]
    for entry in squad
    if entry.get("player_id") is not None
]

duplicates = len(player_ids) - len(set(player_ids))

print("Duplicate player IDs:", duplicates)
print("Data inspection completed.")


import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# 1. Load our Sportmonks API token
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

token = os.getenv("SPORTMONKS_API_TOKEN")

if not token:
    raise SystemExit("Sportmonks API token is missing.")

# 2. Select the player, team and season
player_id = 82032
team_id = 85
season_id = 27897

url = f"https://api.sportmonks.com/v3/football/players/{player_id}"

# 3. Request detailed player statistics
try:
    response = requests.get(
        url,
        headers={"Authorization": token},
        params={"include": "statistics.details.type"},
        timeout=20,
    )

    print("HTTP status:", response.status_code)
    response.raise_for_status()

    player = response.json()["data"]
    print("Player:", player["name"])

    # 4. Find the correct team and season
    records = [
        record
        for record in player.get("statistics", [])
        if record.get("season_id") == season_id
        and record.get("team_id") == team_id
    ]

    if not records:
        print("No statistics found for the selected season and team.")

    # 5. Extract goals and assists
    for record in records:
        print("Season ID:", record["season_id"])

        found = set()

        for detail in record.get("details", []):
            stat_type = detail.get("type") or {}
            stat_name = stat_type.get("name")
            stat_code = stat_type.get("code")
            value = detail.get("value") or {}

            if stat_code in ("goals", "assists"):
                print(f"{stat_name}: {value.get('total')}")
                found.add(stat_code)

        for missing in {"goals", "assists"} - found:
            print(f"{missing.title()}: not available")

except requests.RequestException as error:
    print("API request failed:", type(error).__name__)
except (KeyError, TypeError, ValueError):
    print("Unexpected API response structure.")

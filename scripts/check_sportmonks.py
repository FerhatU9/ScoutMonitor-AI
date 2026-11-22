
import os

import json

from pathlib import Path

import requests
from dotenv import load_dotenv

# 1. Load the API token from our project folder
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

token = os.getenv("SPORTMONKS_API_TOKEN")

if not token:
    raise SystemExit("API token missing. Check your .env file.")

# 2. Choose the football data we want
url = "https://api.sportmonks.com/v3/football/squads/teams/85"

# 3. Request the FC Copenhagen squad
try:
    response = requests.get(
        url,
        headers={"Authorization": token},
        params={"include": "player"},
        timeout=20,
    )

    print("HTTP status:", response.status_code)

    if response.status_code == 200:
        players = response.json().get("data", [])

        print("Squad entries:", len(players))

        for entry in players[:5]:
            player = entry.get("player") or {}
            name = player.get("display_name") or player.get("name")
            print("-", name or "Name unavailable")

        # Save the squad data to a JSON file
        output_file = project_folder / "data" / "fc_copenhagen_squad.json"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", encoding="utf-8") as file:
            json.dump(players, file, indent=2, ensure_ascii=False)

        print("Saved squad to:", output_file)

    else:
        print("API request unsuccessful. Check the status code.")

except requests.RequestException:
    print("Network error. Check your internet connection.")

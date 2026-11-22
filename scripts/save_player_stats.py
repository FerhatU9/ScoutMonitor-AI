
import os
from pathlib import Path

import requests
import psycopg
from dotenv import load_dotenv

# 1. Load our API token and database settings
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

token = os.getenv("SPORTMONKS_API_TOKEN")

if not token:
    raise SystemExit("Sportmonks API token is missing.")

# 2. Select our player, team and season
player_id = 82032
team_id = 85
season_id = 27897

url = f"https://api.sportmonks.com/v3/football/players/{player_id}"

try:
    # 3. Retrieve real statistics
    response = requests.get(
        url,
        headers={"Authorization": token},
        params={"include": "statistics.details.type"},
        timeout=20,
    )

    print("API status:", response.status_code)
    response.raise_for_status()

    player = response.json()["data"]
    print("Player:", player["name"])

    # 4. Find the correct season and team
    records = [
        record
        for record in player.get("statistics", [])
        if record.get("season_id") == season_id
        and record.get("team_id") == team_id
    ]

    if len(records) != 1:
        raise ValueError(
            "Expected exactly one matching season record."
        )

    # 5. Extract goals and assists
    stats = {}

    for detail in records[0].get("details", []):
        stat_type = detail.get("type") or {}
        code = stat_type.get("code")

        if code in ("goals", "assists"):
            value = (detail.get("value") or {}).get("total")

            if type(value) is not int or value < 0:
                raise ValueError(f"Invalid {code} value.")

            if code in stats:
                raise ValueError(f"Duplicate {code} statistic.")

            stats[code] = value

    if "goals" not in stats or "assists" not in stats:
        raise ValueError("Goals or assists are missing.")

    print("Goals:", stats["goals"])
    print("Assists:", stats["assists"])

    # 6. Connect to PostgreSQL
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=10,
    ) as connection:

        with connection.cursor() as cursor:

            # 7. Save the statistics
            cursor.execute(
                """
                INSERT INTO player_season_stats
                (player_id, team_id, season_id,
                 snapshot_date, goals, assists)
                VALUES (%s, %s, %s, CURRENT_DATE, %s, %s)

                ON CONFLICT
                (player_id, team_id, season_id, snapshot_date)

                DO UPDATE SET
                    goals = EXCLUDED.goals,
                    assists = EXCLUDED.assists,
                    retrieved_at = CURRENT_TIMESTAMP;
                """,
                (
                    player_id,
                    team_id,
                    season_id,
                    stats["goals"],
                    stats["assists"],
                ),
            )

    print("Statistics saved successfully!")

except (requests.RequestException, psycopg.Error, ValueError,
        KeyError, TypeError) as error:
    print("Operation failed:", type(error).__name__)
    print("No new statistics were confirmed as saved.")
    raise SystemExit(1)
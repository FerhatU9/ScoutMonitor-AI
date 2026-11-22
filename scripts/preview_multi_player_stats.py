
import os
import time
from pathlib import Path

import psycopg
import requests
from dotenv import load_dotenv


# ========================================
# STEP 1 - LOAD PROJECT SETTINGS
# ========================================

project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

api_token = os.getenv("SPORTMONKS_API_TOKEN")

if not api_token:
    raise SystemExit("Sportmonks API token is missing.")


# ========================================
# STEP 2 - CONFIGURE OUR TEST
# ========================================

TEAM_ID = 85
SEASON_ID = 27897
PLAYER_LIMIT = 3

API_URL = "https://api.sportmonks.com/v3/football/players"


# ========================================
# STEP 3 - CONNECT TO POSTGRESQL
# ========================================

def connect_db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=10,
    )


# ========================================
# STEP 4 - GET PLAYERS FROM DATABASE
# ========================================

def get_players():

    with connect_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT player_id, name
                FROM players
                WHERE team_id = %s
                ORDER BY
                    CASE
                        WHEN player_id = 82032 THEN 0
                        ELSE 1
                    END,
                    name
                LIMIT %s
                """,
                (TEAM_ID, PLAYER_LIMIT),
            )

            return cursor.fetchall()


# ========================================
# STEP 5 - EXTRACT A STATISTIC
# ========================================

def extract_stat(details, code, type_id):

    for detail in details:

        stat_type = detail.get("type") or {}

        matches = (
            stat_type.get("code") == code
            or detail.get("type_id") == type_id
        )

        if not matches:
            continue

        value = detail.get("value")

        if isinstance(value, dict):
            value = value.get("total")

        if value is None or isinstance(value, bool):
            return None

        try:
            number = int(value)

        except (TypeError, ValueError, OverflowError):
            return None

        if str(value) != str(number) or number < 0:
            return None

        return number

    return None


# ========================================
# STEP 6 - REQUEST PLAYER STATISTICS
# ========================================

def fetch_player_stats(player_id):

    url = f"{API_URL}/{player_id}"

    response = requests.get(
        url,
        headers={"Authorization": api_token},
        params={
            "include": "statistics.details.type"
        },
        timeout=(10, 30),
    )

    if response.status_code == 429:
        raise SystemExit(
            "Sportmonks rate limit reached. Stop requests."
        )

    response.raise_for_status()

    player_data = response.json().get("data") or {}

    if player_data.get("id") != player_id:
        return None

    statistics = player_data.get("statistics") or []

    # Find statistics for the correct team and season
    matching = [
        item
        for item in statistics
        if item.get("team_id") == TEAM_ID
        and item.get("season_id") == SEASON_ID
        and item.get("has_values", True) is not False
    ]

    # Avoid using ambiguous season records
    if len(matching) != 1:
        return None

    details = matching[0].get("details") or []

    goals = extract_stat(
        details,
        "goals",
        52,
    )

    assists = extract_stat(
        details,
        "assists",
        79,
    )

    # Important:
    # Missing statistics remain None.
    # We never invent zero values.

    return {
        "goals": goals,
        "assists": assists,
    }


# ========================================
# STEP 7 - RUN MULTI-PLAYER PREVIEW
# ========================================

def main():

    players = get_players()

    print("ScoutMonitor AI - Multi-player Preview")
    print("Players selected:", len(players))
    print("Team ID:", TEAM_ID)
    print("Season ID:", SEASON_ID)

    complete = 0
    partial = 0
    unavailable = 0

    for player_id, name in players:

        print("\n----------------------------")
        print("Player:", name)
        print("Player ID:", player_id)

        try:
            stats = fetch_player_stats(player_id)

            if stats is None:
                print(
                    "Status: No usable team/season record."
                )
                unavailable += 1

            else:
                goals = stats["goals"]
                assists = stats["assists"]

                print(
                    "Goals:",
                    goals if goals is not None
                    else "Not reported"
                )

                print(
                    "Assists:",
                    assists if assists is not None
                    else "Not reported"
                )

                if goals is not None and assists is not None:

                    print("Status: COMPLETE DATA")
                    complete += 1

                elif goals is not None or assists is not None:

                    print("Status: PARTIAL DATA")
                    partial += 1

                else:

                    print(
                        "Status: NO GOALS/ASSISTS REPORTED"
                    )
                    unavailable += 1

        except requests.RequestException as error:

            print(
                "API error:",
                type(error).__name__
            )
            unavailable += 1

        # Avoid sending requests too quickly
        time.sleep(1)

    print("\n----------------------------")
    print("Players checked:", len(players))
    print("Complete data:", complete)
    print("Partial data:", partial)
    print("Unavailable data:", unavailable)
    print("Database changes: NONE")
    print("\nMulti-player preview completed!")


if __name__ == "__main__":
    main()

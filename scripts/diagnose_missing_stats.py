
import requests

from preview_multi_player_stats import (
    API_URL,
    TEAM_ID,
    SEASON_ID,
    api_token,
)

# Players whose statistics were unavailable
players = [
    (37722503, "Akos Markgraf"),
    (4088, "Andreas Cornelius"),
]

for player_id, name in players:

    print("\n-----------------------------")
    print("Checking:", name)
    print("Player ID:", player_id)

    try:
        response = requests.get(
            f"{API_URL}/{player_id}",
            headers={"Authorization": api_token},
            params={
                "include": "statistics.details.type"
            },
            timeout=(10, 30),
        )

        print("HTTP status:", response.status_code)
        response.raise_for_status()

        data = response.json().get("data") or {}
        records = data.get("statistics") or []

        print("Total season records:", len(records))

        matching = [
            record
            for record in records
            if record.get("team_id") == TEAM_ID
            and record.get("season_id") == SEASON_ID
        ]

        print(
            "Matching team and season records:",
            len(matching),
        )

        if not matching:
            print("No matching season statistics.")

            available_seasons = sorted({
                record.get("season_id")
                for record in records
                if record.get("team_id") == TEAM_ID
                and record.get("season_id") is not None
            })

            print(
                "Available seasons for this team:",
                available_seasons,
            )

        for record in matching:

            print("Has values:", record.get("has_values"))

            details = record.get("details") or []

            print("Statistic details:", len(details))

            goals = [
                item.get("value")
                for item in details
                if item.get("type_id") == 52
            ]

            assists = [
                item.get("value")
                for item in details
                if item.get("type_id") == 79
            ]

            print("Goals data:", goals)
            print("Assists data:", assists)

    except requests.RequestException as error:
        print("Request failed:", type(error).__name__)

print("\nDiagnostic completed.")
print("Database changes: NONE")

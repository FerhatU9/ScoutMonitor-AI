
import argparse
import time
from datetime import date

import requests

from preview_multi_player_stats import (
    TEAM_ID,
    SEASON_ID,
    get_players,
    fetch_player_stats,
    connect_db,
)


# ========================================
# STEP 1 - CLASSIFY DATA QUALITY
# ========================================

def classify_stats(goals, assists):

    if goals is not None and assists is not None:
        return "COMPLETE"

    if goals is not None or assists is not None:
        return "PARTIAL"

    return "NOT_REPORTED"


# ========================================
# STEP 2 - COLLECT PLAYER STATISTICS
# ========================================

def collect_players():

    players = get_players()
    observations = []

    for player_id, name in players:

        print("\nPlayer:", name)

        try:
            stats = fetch_player_stats(player_id)

        except requests.RequestException as error:
            print("API error:", type(error).__name__)
            continue

        finally:
            time.sleep(1)

        if stats is None:
            print("Skipped: No usable team/season record.")
            continue

        goals = stats["goals"]
        assists = stats["assists"]

        status = classify_stats(goals, assists)

        print("Goals:", goals)
        print("Assists:", assists)
        print("Data status:", status)

        observations.append(
            (
                player_id,
                TEAM_ID,
                SEASON_ID,
                date.today(),
                goals,
                assists,
                status,
            )
        )

    return observations


# ========================================
# STEP 3 - COUNT DATABASE RECORDS
# ========================================

def count_records():

    with connect_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) FROM player_stat_observations"
            )

            return cursor.fetchone()[0]


# ========================================
# STEP 4 - INSERT INTO POSTGRESQL
# ========================================

def store_observations(observations, save=False):

    with connect_db() as connection:

        with connection.cursor() as cursor:

            for observation in observations:

                cursor.execute(
                    """
                    INSERT INTO player_stat_observations (
                        player_id,
                        team_id,
                        season_id,
                        snapshot_date,
                        goals,
                        assists,
                        data_status
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (
                        player_id,
                        team_id,
                        season_id,
                        snapshot_date
                    )
                    DO NOTHING
                    RETURNING player_id
                    """,
                    observation,
                )

                inserted = cursor.fetchone()

                if inserted:
                    print(
                        "Inserted player:",
                        observation[0]
                    )
                else:
                    print(
                        "Already exists, skipped:",
                        observation[0]
                    )

        if not save:
            # Safe test: undo all temporary inserts
            connection.rollback()
            print("\nTEST MODE: All inserts rolled back.")

    # When save=True, successful completion commits
    # the transaction automatically.


# ========================================
# STEP 5 - RUN APPLICATION
# ========================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--save",
        action="store_true",
        help="Permanently save statistics",
    )

    args = parser.parse_args()

    print("ScoutMonitor AI - Multi-player Storage")

    if args.save:
        print("Mode: PERMANENT SAVE")
    else:
        print("Mode: SAFE TEST")

    before = count_records()

    observations = collect_players()

    print("\nObservations collected:", len(observations))

    if not observations:
        print("No observations to store.")
        return

    store_observations(
        observations,
        save=args.save,
    )

    after = count_records()

    print("\nRecords before:", before)
    print("Records after:", after)

    if not args.save:
        assert before == after
        print("PASS: Database unchanged after test.")
    else:
        print("Storage operation committed.")

    print("\nMulti-player storage workflow completed!")


if __name__ == "__main__":
    main()

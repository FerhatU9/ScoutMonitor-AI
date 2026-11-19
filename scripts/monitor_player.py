
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Import our shared monitoring function
from monitor_logic import detect_change

from alert_logic import create_alert

from alert_storage import save_alert

# 1. Load database settings
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

# 2. Select the player to monitor
player_id = 82032
team_id = 85
season_id = 27897

# 3. Retrieve the two most recent snapshots
sql = """
SELECT snapshot_date, goals, assists
FROM player_season_stats
WHERE player_id = %s
  AND team_id = %s
  AND season_id = %s
ORDER BY snapshot_date DESC
LIMIT 2;
"""

try:
    # 4. Connect to PostgreSQL
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=10,
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(sql, (player_id, team_id, season_id))
            snapshots = cursor.fetchall()

    print("Monitoring player:", player_id)

    # 5. Get the latest statistics
    if not snapshots:
        status = detect_change(None, None)

    else:
        latest_date, goals, assists = snapshots[0]

        print("Latest snapshot:", latest_date)
        print("Goals:", goals)
        print("Assists:", assists)

        # 6. Get the previous statistics if available
        previous = None

        if len(snapshots) == 2:
            previous_date, old_goals, old_assists = snapshots[1]
            previous = (old_goals, old_assists)

            print("Previous snapshot:", previous_date)

        # 7. Use our shared function
        current = (goals, assists)
        status = detect_change(previous, current)


        # Create an alert only if performance increased

        # Create and save verified performance alerts
        if status == "CHANGE_DETECTED":
            alert = create_alert("Alex Král", previous, current)

            if alert:
                print(alert)

                save_alert(
                    player_id=player_id,
                    team_id=team_id,
                    season_id=season_id,
                    previous_date=previous_date,
                    current_date=latest_date,
                    goals_increase=goals - old_goals,
                    assists_increase=assists - old_assists,
                    message=alert,
                )

        # 8. Show the changes when values are available
        if previous is not None:
            if None not in current and None not in previous:
                print("New goals:", goals - old_goals)
                print("New assists:", assists - old_assists)

    print("Monitoring status:", status)

except psycopg.Error as error:
    print("Database error:", type(error).__name__)

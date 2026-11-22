
import os
from pathlib import Path
from contextlib import nullcontext

import psycopg
from dotenv import load_dotenv


def save_alert(
    player_id,
    team_id,
    season_id,
    previous_date,
    current_date,
    goals_increase,
    assists_increase,
    message,
    connection=None,
):
    project_folder = Path(__file__).resolve().parent.parent
    load_dotenv(project_folder / ".env")

    sql = """
    INSERT INTO performance_alerts (
        player_id,
        team_id,
        season_id,
        previous_snapshot_date,
        current_snapshot_date,
        goals_increase,
        assists_increase,
        message
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

    ON CONFLICT ON CONSTRAINT unique_performance_alert
    DO NOTHING

    RETURNING alert_id;
    """

    # Normal operation: Create our own database connection
    if connection is None:
        context = psycopg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            connect_timeout=10,
        )

    # Testing: Reuse a connection managed by the test
    else:
        context = nullcontext(connection)

    with context as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    player_id,
                    team_id,
                    season_id,
                    previous_date,
                    current_date,
                    goals_increase,
                    assists_increase,
                    message,
                ),
            )

            result = cursor.fetchone()

    if result:
        print("New alert saved! ID:", result[0])
        return True

    print("Alert already exists. Duplicate prevented.")
    return False

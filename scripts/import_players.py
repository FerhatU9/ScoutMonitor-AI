
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# 1. Find our project folder and load database settings
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

# 2. Read the saved football data
file_path = project_folder / "data" / "fc_copenhagen_squad.json"

with file_path.open("r", encoding="utf-8") as file:
    squad = json.load(file)

# 3. Prepare the SQL command
sql = """
INSERT INTO players (player_id, name, team_id, jersey_number)
VALUES (%s, %s, %s, %s)
ON CONFLICT (player_id)
DO UPDATE SET
    name = EXCLUDED.name,
    team_id = EXCLUDED.team_id,
    jersey_number = EXCLUDED.jersey_number;
"""

# 4. Connect Python to PostgreSQL
try:
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=10,
    ) as connection:

        with connection.cursor() as cursor:
            imported = 0

            # 5. Import each player
            for entry in squad:
                player = entry.get("player") or {}
                player_id = entry.get("player_id")
                name = player.get("display_name") or player.get("name")

                if player_id is None or not name:
                    continue

                cursor.execute(
                    sql,
                    (
                        player_id,
                        name,
                        entry.get("team_id"),
                        entry.get("jersey_number"),
                    ),
                )

                imported += 1

            # 6. Check how many players are stored
            cursor.execute("SELECT COUNT(*) FROM players;")
            total = cursor.fetchone()[0]

    print("Database connection successful!")
    print("Players processed:", imported)
    print("Total players in database:", total)

except psycopg.Error:
    print("Database operation failed.")
    print("Check your database settings and PostgreSQL server.")

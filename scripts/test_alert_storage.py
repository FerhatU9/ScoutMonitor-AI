
import os
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from alert_storage import save_alert

# Load database settings
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")


def connect_db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=10,
    )


# Fictional alert for testing only
test_alert = {
    "player_id": 82032,
    "team_id": 85,
    "season_id": 27897,
    "previous_date": date(2026, 11, 13),
    "current_date": date(2026, 11, 14),
    "goals_increase": 1,
    "assists_increase": 1,
    "message": "TEST ONLY: Fictional performance increase",
}

connection = connect_db()

try:
    # Count existing alerts
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM performance_alerts")
        before = cursor.fetchone()[0]

    # Attempt to save the same alert twice
    first = save_alert(connection=connection, **test_alert)
    second = save_alert(connection=connection, **test_alert)

    # Check how many alerts exist during the test
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM performance_alerts")
        during = cursor.fetchone()[0]

    assert first is True
    assert second is False
    assert during == before + 1

    print("PASS: First alert inserted")
    print("PASS: Duplicate prevented")
    print("Alerts during test:", during)

finally:
    # Always cancel the fictional database changes
    connection.rollback()
    connection.close()
    print("Test transaction rolled back.")


# Verify the database contains no additional alerts
with connect_db() as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM performance_alerts")
        after = cursor.fetchone()[0]

assert after == before

print("PASS: Database unchanged after rollback")
print("Alerts after rollback:", after)
print("\nAll alert storage tests passed!")

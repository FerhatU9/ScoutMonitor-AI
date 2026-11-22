import os
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from report_storage import save_pending_report

# Load existing database settings
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


# Test report based on our previously verified snapshot
test_report = {
    "player_id": 82032,
    "snapshot_date": "2026-11-16",
    "goals": 1,
    "assists": 2,
    "monitoring_status": "WAITING_FOR_HISTORY",
    "analysis": (
        "TEST ONLY: Historical comparison is unavailable."
    ),
}


# Open a database connection
connection = connect_db()

try:
    # Count reports before the test
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM ai_reports")
        before = cursor.fetchone()[0]

    # Insert our test report
    report_id = save_pending_report(
        connection=connection,
        player_id=82032,
        team_id=85,
        season_id=27897,
        snapshot_date=test_report["snapshot_date"],
        model_name="TEST_ONLY_NO_LLM",
        report_data=test_report,
    )

    print("Test report inserted:", report_id)

    # Confirm PostgreSQL stored it correctly
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT review_status, validation_status
            FROM ai_reports
            WHERE report_id = %s
            """,
            (report_id,),
        )

        saved = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM ai_reports")
        during = cursor.fetchone()[0]

    assert saved == ("PENDING", "PASS")
    assert during == before + 1

    print("PASS: Report inserted")
    print("PASS: Report status is PENDING")
    print("PASS: Validation status is PASS")

finally:
    # Always undo the test insert
    connection.rollback()
    connection.close()
    print("PASS: Test transaction rolled back")


# Check that the database remains unchanged
with connect_db() as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM ai_reports")
        after = cursor.fetchone()[0]

assert after == before

print("PASS: Database unchanged")
print("Reports after test:", after)
print("\nAll report storage tests passed!")
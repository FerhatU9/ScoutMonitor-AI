
import os
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from report_storage import save_pending_report
from review_actions import review_report


# Load our database settings
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


# Use fictional report content for testing
test_report = {
    "player_id": 82032,
    "snapshot_date": "2026-11-16",
    "goals": 1,
    "assists": 2,
    "monitoring_status": "WAITING_FOR_HISTORY",
    "analysis": "TEST ONLY: Historical comparison unavailable.",
}


def create_test_report(connection):
    return save_pending_report(
        connection=connection,
        player_id=82032,
        team_id=85,
        season_id=27897,
        snapshot_date=test_report["snapshot_date"],
        model_name="TEST_ONLY_NO_LLM",
        report_data=test_report,
    )


connection = connect_db()

try:
    # Count existing reports
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM ai_reports")
        before = cursor.fetchone()[0]

    # Create three temporary reports
    approved_id = create_test_report(connection)
    rejected_id = create_test_report(connection)
    blocked_id = create_test_report(connection)

    # TEST 1 - Approve a validated report
    approved = review_report(
        connection,
        approved_id,
        "APPROVED",
        "Test Reviewer",
    )

    assert approved["review_status"] == "APPROVED"
    print("PASS: Validated report approved")

    # TEST 2 - Reject a report with a reason
    rejected = review_report(
        connection,
        rejected_id,
        "REJECTED",
        "Test Reviewer",
        "Fictional report rejected for testing.",
    )

    assert rejected["review_status"] == "REJECTED"
    print("PASS: Report rejected with reason")

    # TEST 3 - Prevent reviewing the same report twice
    try:
        review_report(
            connection,
            approved_id,
            "REJECTED",
            "Test Reviewer",
            "Attempting a second decision.",
        )
    except ValueError:
        print("PASS: Second review prevented")
    else:
        raise AssertionError("Second review was allowed.")

    # TEST 4 - Simulate a report that failed validation
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE ai_reports
            SET validation_status = 'REVIEW_REQUIRED'
            WHERE report_id = %s
            """,
            (blocked_id,),
        )

    # Attempt to approve this unvalidated report
    try:
        review_report(
            connection,
            blocked_id,
            "APPROVED",
            "Test Reviewer",
        )
    except ValueError:
        print("PASS: Unvalidated approval prevented")
    else:
        raise AssertionError(
            "Unvalidated report was approved."
        )

    # Verify the report remains pending
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT review_status
            FROM ai_reports
            WHERE report_id = %s
            """,
            (blocked_id,),
        )
        assert cursor.fetchone()[0] == "PENDING"

        cursor.execute("SELECT COUNT(*) FROM ai_reports")
        during = cursor.fetchone()[0]

    assert during == before + 3
    print("PASS: Review statuses verified")

finally:
    # Undo all fictional changes
    connection.rollback()
    connection.close()
    print("PASS: Test transaction rolled back")


# Confirm the real database was not changed
with connect_db() as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM ai_reports")
        after = cursor.fetchone()[0]

assert after == before

print("PASS: Database unchanged")
print("Reports after test:", after)
print("\nAll human review tests passed!")

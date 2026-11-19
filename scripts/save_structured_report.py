
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from scout_structured_graph import graph
from report_storage import save_pending_report


# ========================================
# STEP 1 - LOAD PROJECT SETTINGS
# ========================================

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


# ========================================
# STEP 2 - DEFINE PLAYER INFORMATION
# ========================================

player_id = 82032
team_id = 85
season_id = 27897


# ========================================
# STEP 3 - RUN LANGGRAPH AND GEMINI
# ========================================

def main():

    print("Starting ScoutMonitor AI report generation...")

    result = graph.invoke({
        "player_id": player_id,
        "team_id": team_id,
        "season_id": season_id,
    })

    report = result.get("structured_report") or {}
    validation = result.get("validation_status", "")

    print("\nValidation result:", validation)

    # Do not save failed or incomplete AI reports
    if not validation.startswith(
        "PASS - all 5 factual fields match."
    ):
        print("Report NOT saved: Validation did not pass.")
        return

    if not report:
        print("Report NOT saved: No AI report available.")
        return

    snapshots = result.get("snapshots") or []

    if not snapshots:
        print("Report NOT saved: No source statistics.")
        return

    latest_date, goals, assists = snapshots[0]

    # Double-check the five factual fields
    expected = {
        "player_id": player_id,
        "snapshot_date": str(latest_date),
        "goals": goals,
        "assists": assists,
        "monitoring_status": result["status"],
    }

    incorrect_fields = [
        field
        for field, value in expected.items()
        if report.get(field) != value
    ]

    if incorrect_fields:
        print("Report NOT saved: Factual mismatch.")
        print("Incorrect fields:", incorrect_fields)
        return

    if not str(report.get("analysis", "")).strip():
        print("Report NOT saved: Analysis is empty.")
        return

    model_name = os.getenv("GEMINI_MODEL")

    if not model_name:
        print("Report NOT saved: Gemini model not set.")
        return

    # ========================================
    # STEP 4 - SAVE TO POSTGRESQL
    # ========================================

    with connect_db() as connection:

        # Avoid saving duplicate reports for the
        # same player, snapshot and AI model
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT report_id
                FROM ai_reports
                WHERE player_id = %s
                  AND team_id = %s
                  AND season_id = %s
                  AND snapshot_date = %s
                  AND model_name = %s
                LIMIT 1
                """,
                (
                    player_id,
                    team_id,
                    season_id,
                    latest_date,
                    model_name,
                ),
            )

            existing = cursor.fetchone()

        if existing:
            print(
                "A report already exists. Report ID:",
                existing[0],
            )
            print("No duplicate report saved.")
            return

        report_id = save_pending_report(
            connection=connection,
            player_id=player_id,
            team_id=team_id,
            season_id=season_id,
            snapshot_date=latest_date,
            model_name=model_name,
            report_data=report,
        )

        # The connection context commits
        # automatically when there is no error.

    # ========================================
    # STEP 5 - DISPLAY RESULT
    # ========================================

    print("\n--- REPORT SAVED SUCCESSFULLY ---")
    print("Report ID:", report_id)
    print("Player ID:", player_id)
    print("Snapshot date:", latest_date)
    print("Goals:", goals)
    print("Assists:", assists)
    print("Validation status: PASS")
    print("Review status: PENDING")
    print("\nOpen the Streamlit dashboard to review.")


if __name__ == "__main__":
    main()

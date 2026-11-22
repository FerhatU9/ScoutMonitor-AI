
import os
from pathlib import Path

import psycopg
import streamlit as st
from dotenv import load_dotenv

from review_actions import review_report


# ========================================
# STEP 1 - LOAD DATABASE SETTINGS
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
# STEP 2 - LOAD PENDING REPORTS
# ========================================

def get_pending_reports():

    with connect_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    report_id,
                    player_id,
                    snapshot_date,
                    model_name,
                    validation_status,
                    report_data
                FROM ai_reports
                WHERE review_status = 'PENDING'
                ORDER BY created_at DESC, report_id DESC
                LIMIT 50
            """)

            rows = cursor.fetchall()

    reports = []

    for row in rows:
        reports.append({
            "report_id": row[0],
            "player_id": row[1],
            "snapshot_date": row[2],
            "model_name": row[3],
            "validation_status": row[4],
            "report_data": row[5],
        })

    return reports


# ========================================
# STEP 3 - BUILD THE DASHBOARD
# ========================================

st.set_page_config(
    page_title="ScoutMonitor AI - Review",
    layout="wide",
)

st.title("ScoutMonitor AI")
st.subheader("Football Intelligence - Human Review")

st.caption(
    "Local development dashboard. "
    "Reports are not published automatically."
)

# Display confirmation after saving a decision
if "review_message" in st.session_state:
    st.success(st.session_state.pop("review_message"))


# ========================================
# STEP 4 - RETRIEVE REPORTS
# ========================================

try:
    reports = get_pending_reports()

except psycopg.Error:
    st.error(
        "Could not connect to PostgreSQL. "
        "Check your database settings and server."
    )
    st.stop()

st.metric("Pending Reports", len(reports))

if st.button("Refresh Reports"):
    st.rerun()

# ========================================
# REPORT HISTORY - APPROVED AND REJECTED
# ========================================

st.divider()
st.subheader("Report History")

try:
    with connect_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    report_id,
                    player_id,
                    snapshot_date,
                    model_name,
                    validation_status,
                    review_status,
                    reviewer_name,
                    review_notes,
                    reviewed_at,
                    report_data
                FROM ai_reports
                WHERE review_status IN ('APPROVED', 'REJECTED')
                ORDER BY reviewed_at DESC, report_id DESC
                LIMIT 50
            """)

            history = cursor.fetchall()

except psycopg.Error:
    st.error("Could not load report history.")
    history = []


st.metric("Reviewed Reports (latest 50)", len(history))

if history:

    history_options = {
        row[0]: row for row in history
    }

    selected_history_id = st.selectbox(
        "Select a previously reviewed report",
        options=list(history_options),
        format_func=lambda report_id: (
            f"Report #{report_id} - "
            f"{history_options[report_id][5]}"
        ),
        key="report_history_selection",
    )

    selected_history = history_options[selected_history_id]

    st.write("Player ID:", selected_history[1])
    st.write("Snapshot date:", selected_history[2])
    st.write("AI model:", selected_history[3])
    st.write("Validation:", selected_history[4])
    st.write("Review status:", selected_history[5])
    st.write("Reviewer:", selected_history[6])
    st.write("Review notes:", selected_history[7] or "None")
    st.write("Reviewed at:", selected_history[8])

    with st.expander("View complete AI report"):
        st.json(selected_history[9])

else:
    st.info("No approved or rejected reports yet.")

st.divider()


# ========================================
# MULTI-PLAYER STATISTICS DASHBOARD
# ========================================

st.divider()
st.subheader("Multi-Player Statistics")

TEAM_ID = 85
SEASON_ID = 27897

try:
    with connect_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.player_id,
                    p.name,
                    s.snapshot_date,
                    s.goals,
                    s.assists,
                    s.data_status
                FROM players AS p

                LEFT JOIN LATERAL (
                    SELECT
                        snapshot_date,
                        goals,
                        assists,
                        data_status
                    FROM player_stat_observations
                    WHERE player_id = p.player_id
                      AND team_id = %s
                      AND season_id = %s
                    ORDER BY
                        snapshot_date DESC,
                        collected_at DESC
                    LIMIT 1
                ) AS s ON TRUE

                WHERE p.team_id = %s
                ORDER BY p.name
                """,
                (TEAM_ID, SEASON_ID, TEAM_ID),
            )

            player_stats = cursor.fetchall()

except psycopg.Error:
    st.error("Unable to load player statistics.")
    player_stats = []


if player_stats:

    complete = sum(
        row[5] == "COMPLETE"
        for row in player_stats
    )

    partial = sum(
        row[5] == "PARTIAL"
        for row in player_stats
    )

    not_reported = sum(
        row[5] == "NOT_REPORTED"
        for row in player_stats
    )

    not_collected = sum(
        row[5] is None
        for row in player_stats
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Complete", complete)
    col2.metric("Partial", partial)
    col3.metric("Not Reported", not_reported)
    col4.metric("Not Collected", not_collected)

    table_data = []

    for row in player_stats:

        player_id, name, snapshot, goals, assists, status = row

        table_data.append({
            "Player": name,
            "Player ID": player_id,
            "Snapshot": str(snapshot) if snapshot else "-",
            "Goals": (
                goals if goals is not None
                else "Not reported" if status else "-"
            ),
            "Assists": (
                assists if assists is not None
                else "Not reported" if status else "-"
            ),
            "Data Status": status or "NOT_COLLECTED",
        })



    display_table_data = [
        {
            **row,
            "Goals": str(row["Goals"]),
            "Assists": str(row["Assists"]),
        }
        for row in table_data
    ]

    st.dataframe(
        display_table_data,
        width="stretch",
        hide_index=True,
    )



    # ========================================
    # SELECT A PLAYER
    # ========================================

    st.divider()
    st.subheader("Select a Player")

    player_lookup = {
        row[0]: row
        for row in player_stats
    }

    selected_player_id = st.selectbox(
        "Choose a player to inspect",
        options=list(player_lookup.keys()),
        format_func=lambda player_id: (
            f"{player_lookup[player_id][1]} "
            f"(ID: {player_id})"
        ),
        key="scout_selected_player",
    )

    selected_player = player_lookup[selected_player_id]

    player_id, name, snapshot, goals, assists, status = (
        selected_player
    )

    st.write("**Selected player:**", name)
    st.write("**Player ID:**", player_id)
    st.write(
        "**Latest snapshot:**",
        str(snapshot) if snapshot else "Not collected"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Goals",
        goals if goals is not None else "Not reported"
    )

    col2.metric(
        "Assists",
        assists if assists is not None else "Not reported"
    )

    # Check whether the player has sufficient data
    # for our current AI report workflow.



    if status == "COMPLETE":
        st.success(
            "Complete statistics available. "
            "This player is eligible for AI report generation."
        )

        preview_key = "scout_ai_report_preview"

        # STEP 1: Generate the report
        if st.button(
            "Generate AI Report (Preview)",
            key="generate_selected_player_report",
        ):
            # Remove any previous preview
            st.session_state.pop(preview_key, None)

            try:
                from scout_structured_graph import graph

                with st.spinner(
                    "Generating and validating AI report..."
                ):
                    result = graph.invoke({
                        "player_id": int(player_id),
                        "team_id": TEAM_ID,
                        "season_id": SEASON_ID,
                    })

                report = result.get("structured_report")
                validation = str(
                    result.get("validation_status", "")
                )

                if not isinstance(report, dict) or not report:
                    st.warning(
                        "No structured AI report was generated."
                    )
                else:
                    # Remember the generated report
                    st.session_state[preview_key] = {
                        "player_id": int(player_id),
                        "snapshot_date": str(snapshot),
                        "report": report,
                        "validation": validation,
                        "summary": result.get("summary", ""),
                    }

            except Exception as error:
                st.error(
                    "AI generation failed: "
                    f"{type(error).__name__}"
                )

        # STEP 2: Retrieve the saved preview
        preview = st.session_state.get(preview_key)

        if (
            preview
            and preview["player_id"] == int(player_id)
            and preview["snapshot_date"] == str(snapshot)
        ):
            st.subheader("AI Scouting Report Preview")

            st.write("**Database Evidence**")
            st.text(preview["summary"])

            st.write("**AI-Generated Report**")
            st.json(preview["report"])

            validation = preview["validation"]

            st.write("**Automatic Validation**")
            st.write(validation)

            # Only validated reports may be submitted
            validation_passed = validation.startswith("PASS")

            if not validation_passed:
                st.error(
                    "The report did not pass factual validation. "
                    "Submission is disabled."
                )

            else:
                st.success(
                    "Factual validation passed. "
                    "Human review is still required."
                )

                # STEP 3: Submit the report for review
                if st.button(
                    "Submit for Human Review",
                    key="submit_selected_report",
                    type="primary",
                ):
                    try:
                        from report_storage import (
                            save_pending_report
                        )

                        report = preview["report"]

                        with connect_db() as connection:

                            # Check for an existing report
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    """
                                    SELECT report_id
                                    FROM ai_reports
                                    WHERE player_id = %s
                                      AND team_id = %s
                                      AND season_id = %s
                                      AND snapshot_date = %s
                                    ORDER BY report_id DESC
                                    LIMIT 1
                                    """,
                                    (
                                        int(player_id),
                                        TEAM_ID,
                                        SEASON_ID,
                                        snapshot,
                                    ),
                                )

                                existing = cursor.fetchone()

                            if existing:
                                st.warning(
                                    "A report already exists for "
                                    f"this player and snapshot. "
                                    f"Report ID: {existing[0]}"
                                )

                            else:
                                report_id = save_pending_report(
                                    connection=connection,
                                    player_id=int(player_id),
                                    team_id=TEAM_ID,
                                    season_id=SEASON_ID,
                                    snapshot_date=snapshot,
                                    model_name="gemini-3.5-flash-lite",
                                    report_data=report,
                                )

                        if not existing:
                            st.session_state.pop(
                                preview_key, None
                            )

                            st.success(
                                f"Report #{report_id} saved! "
                                "Status: PENDING human review."
                            )

                    except Exception as error:
                        st.error(
                            "Report submission failed: "
                            f"{type(error).__name__}"
                        )

            st.caption(
                "AI reports require human approval. "
                "Submission does not publish a report."
            )



    elif status == "PARTIAL":
        st.warning(
            "Partial statistics available. "
            "Some values are missing, so report generation "
            "is not yet enabled for this player."
        )



    elif status == "NOT_REPORTED":
        st.info(
            "Goals and assists have not been reported "
            "for this player's selected season."
        )

    else:
        st.info(
            "Statistics have not yet been collected "
            "for this player."
        )

    st.caption(
        "Missing values are not assumed to be zero. "
        "NOT_COLLECTED means no observation is saved."
    )


else:
    st.info("No players found for the selected team.")

if not reports:
    st.info(
        "No pending reports yet. "
        "The database connection is working, "
        "but no reports are waiting for review."
    )
    st.stop()


# ========================================
# STEP 5 - SELECT A REPORT
# ========================================

report_options = {
    report["report_id"]: (
        f"Report #{report['report_id']} - "
        f"Player {report['player_id']}"
    )
    for report in reports
}

selected_id = st.selectbox(
    "Choose a report",
    options=list(report_options),
    format_func=lambda value: report_options[value],
)

selected = next(
    report
    for report in reports
    if report["report_id"] == selected_id
)


# ========================================
# STEP 6 - DISPLAY REPORT CONTENT
# ========================================

st.subheader("Report Details")

st.write("Player ID:", selected["player_id"])
st.write("Snapshot date:", selected["snapshot_date"])
st.write("AI model:", selected["model_name"])
st.write(
    "Validation status:",
    selected["validation_status"],
)

st.subheader("AI Football Report")
st.json(selected["report_data"])

st.warning(
    "Automated validation checks selected factual "
    "fields only. The reviewer must also inspect "
    "the narrative for unsupported claims."
)


# ========================================
# STEP 7 - HUMAN REVIEW FORM
# ========================================

st.subheader("Review Decision")

with st.form("review_form"):

    reviewer_name = st.text_input(
        "Reviewer name"
    )

    decision = st.radio(
        "Decision",
        ["APPROVED", "REJECTED"],
        horizontal=True,
    )

    review_notes = st.text_area(
        "Review notes (required for rejection)"
    )

    confirmed = st.checkbox(
        "I have reviewed the report and its evidence."
    )

    submitted = st.form_submit_button(
        "Save Review Decision"
    )


# ========================================
# STEP 8 - SAVE THE HUMAN DECISION
# ========================================

if submitted:

    if not confirmed:
        st.error(
            "Please confirm that you reviewed the report."
        )

    elif not reviewer_name.strip():
        st.error("Reviewer name is required.")

    elif decision == "REJECTED" and not review_notes.strip():
        st.error("Please provide a rejection reason.")

    elif (
        decision == "APPROVED"
        and selected["validation_status"] != "PASS"
    ):
        st.error(
            "A report cannot be approved "
            "unless validation passed."
        )

    else:
        try:
            with connect_db() as connection:

                result = review_report(
                    connection=connection,
                    report_id=selected_id,
                    decision=decision,
                    reviewer_name=reviewer_name,
                    review_notes=review_notes.strip() or None,
                )

            # A successful connection context commits
            # the review decision to PostgreSQL.

            st.session_state["review_message"] = (
                f"Report #{result['report_id']} "
                f"was {result['review_status']}."
            )

            st.rerun()

        except (ValueError, psycopg.Error) as error:
            st.error(
                f"Could not save review decision: {error}"
            )

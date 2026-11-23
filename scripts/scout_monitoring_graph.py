
import os
from pathlib import Path
from typing import TypedDict, NotRequired

import psycopg
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from monitor_logic import detect_change

# Load database settings
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")


# State = information shared between workflow steps
class ScoutState(TypedDict):
    player_id: int
    team_id: int
    season_id: int
    snapshots: NotRequired[list[tuple]]
    status: NotRequired[str]
    summary: NotRequired[str]


# Node 1: Retrieve real football statistics
def fetch_snapshots(state: ScoutState):
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=10,
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(
                """
            SELECT snapshot_date, goals, assists
FROM player_stat_observations
WHERE player_id = %s
  AND team_id = %s
  AND season_id = %s
  AND data_status = 'COMPLETE'
  AND goals IS NOT NULL
  AND assists IS NOT NULL
ORDER BY snapshot_date DESC
LIMIT 2;
                """,
                (
                    state["player_id"],
                    state["team_id"],
                    state["season_id"],
                ),
            )
            rows = cursor.fetchall()

    return {"snapshots": rows}


# Node 2: Use our existing monitoring rules
def assess_change(state: ScoutState):
    snapshots = state["snapshots"]

    current = None
    previous = None

    if snapshots:
        current = (snapshots[0][1], snapshots[0][2])

    if len(snapshots) > 1:
        previous = (snapshots[1][1], snapshots[1][2])

    return {"status": detect_change(previous, current)}


# Node 3: Prepare a factual summary
def prepare_summary(state: ScoutState):
    snapshots = state["snapshots"]

    if not snapshots:
        message = "No player statistics available."
    else:
        latest = snapshots[0]
        message = (
            f"Player ID: {state['player_id']}\n"
            f"Snapshot date: {latest[0]}\n"
            f"Goals: {latest[1]}\n"
            f"Assists: {latest[2]}\n"
            f"Monitoring status: {state['status']}"
        )

    return {"summary": message}


# Decide which path LangGraph should follow
def choose_next_step(state: ScoutState):

    if state["status"] == "CHANGE_DETECTED":
        print("Selected graph route: alert")
        return "alert"

    print("Selected graph route: summary")
    return "summary"


# Prepare a draft when performance increases
def prepare_alert_draft(state: ScoutState):

    latest, previous = state["snapshots"][:2]

    latest_date, goals, assists = latest
    previous_date, old_goals, old_assists = previous

    new_goals = goals - old_goals
    new_assists = assists - old_assists

    # Database observations do not by themselves establish provider provenance.
    source_label = (
        "Fictional demonstration data"
        if os.getenv("DB_NAME") == "scoutmonitor_demo"
        else "Stored football observations (provider not independently verified)"
    )

    message = (
        "PERFORMANCE ALERT — REVIEW REQUIRED\n"
        f"Player ID: {state['player_id']}\n"
        f"Previous snapshot: {previous_date}\n"
        f"Current snapshot: {latest_date}\n"
        f"Additional goals: {new_goals}\n"
        f"Additional assists: {new_assists}\n"
        f"Source: {source_label}\n"
        "Note: Changes between snapshots do not "
        "necessarily represent one match."
    )

    return {"summary": message}


# Build the LangGraph monitoring workflow
workflow = StateGraph(ScoutState)

# Register our four nodes
workflow.add_node("fetch_data", fetch_snapshots)
workflow.add_node("check_change", assess_change)
workflow.add_node("create_summary", prepare_summary)
workflow.add_node("create_alert_draft", prepare_alert_draft)

# Retrieve data and assess changes
workflow.add_edge(START, "fetch_data")
workflow.add_edge("fetch_data", "check_change")

# Choose the next step based on monitoring status
workflow.add_conditional_edges(
    "check_change",
    choose_next_step,
    {
        "alert": "create_alert_draft",
        "summary": "create_summary",
    },
)

# Both paths end after their work is finished
workflow.add_edge("create_summary", END)
workflow.add_edge("create_alert_draft", END)

# Prepare the workflow for execution
graph = workflow.compile()


# Run the monitoring workflow

if __name__ == "__main__":
    result = graph.invoke({
        "player_id": 82032,
        "team_id": 85,
        "season_id": 27897,
    })

    print("ScoutMonitor AI — LangGraph Result")
    print(result["summary"])

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from scout_monitoring_graph import graph


# 1. Load our existing settings
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")


# 2. Define the report structure
class FootballReport(BaseModel):
    player_id: int
    snapshot_date: str
    goals: int
    assists: int
    monitoring_status: str

    analysis: str = Field(
        description=(
            "A short factual football analysis using "
            "only the supplied evidence."
        )
    )


# 3. Retrieve verified PostgreSQL evidence
result = graph.invoke({
    "player_id": 82032,
    "team_id": 85,
    "season_id": 27897,
})

snapshots = result["snapshots"]
status = result["status"]

if not snapshots or status in (
    "NO_DATA",
    "MISSING_STATS",
    "REVIEW_DATA",
):
    raise SystemExit(
        "Report generation skipped: data requires review."
    )

latest_date, goals, assists = snapshots[0]

evidence = (
    f"Player ID: {result['player_id']}\n"
    f"Snapshot date: {latest_date}\n"
    f"Goals: {goals}\n"
    f"Assists: {assists}\n"
    f"Monitoring status: {status}"
)


# 4. Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GEMINI_MODEL")

if not api_key or not model_name:
    raise SystemExit("Gemini settings are missing.")


model = ChatGoogleGenerativeAI(
    model=model_name,
    api_key=api_key,
    temperature=0,
    timeout=90,
    max_retries=1,
)


# Tell Gemini to return our defined structure
structured_model = model.with_structured_output(
    FootballReport,
    method="json_schema",
)


# 5. Generate the structured report
report = structured_model.invoke([
    (
        "system",
        "You are ScoutMonitor AI. Use only the "
        "provided football evidence. Copy all factual "
        "fields exactly. Do not invent matches, dates, "
        "statistics, or performance trends. "
        "When history is unavailable, clearly state "
        "that comparisons cannot be made."
    ),
    (
        "human",
        "Prepare a structured football report:\n\n"
        + evidence
    ),
])


# 6. Compare structured fields with PostgreSQL
checks = {
    "player_id": (
        report.player_id == result["player_id"]
    ),
    "snapshot_date": (
        report.snapshot_date == str(latest_date)
    ),
    "goals": report.goals == goals,
    "assists": report.assists == assists,
    "monitoring_status": (
        report.monitoring_status == status
    ),
}

print("\n--- STRUCTURED REPORT ---")
print(report.model_dump_json(indent=2))

print("\n--- STRUCTURED VALIDATION ---")

for field, passed in checks.items():
    print(f"{field}: {'PASS' if passed else 'FAIL'}")

if all(checks.values()):
    print("\nPASS: All 5 factual fields match PostgreSQL.")
    print("Narrative analysis still requires human review.")
else:
    print("\nREVIEW_REQUIRED: Factual mismatch detected.")
    raise SystemExit(1)

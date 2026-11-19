
import re


def validate_report(player_id, snapshot, status, report):
    # Extract the trusted database values
    snapshot_date, goals, assists = snapshot

    # Remove common Markdown formatting
    clean_report = re.sub(r"[*`]", "", report)

    # Define the facts we want to check
    checks = {
        "Player ID": (
            r"\bPlayer\s+ID\s*:\s*(\d+)\b",
            str(player_id),
        ),
        "Snapshot date": (
            r"\bSnapshot\s+Date\s*:\s*(\d{4}-\d{2}-\d{2})\b",
            str(snapshot_date),
        ),
        "Goals": (
            r"\bGoals\s*:\s*(-?\d+)\b",
            str(goals),
        ),
        "Assists": (
            r"\bAssists\s*:\s*(-?\d+)\b",
            str(assists),
        ),
        "Monitoring status": (
            r"\bMonitoring\s+Status\s*:\s*([A-Za-z_]+)\b",
            status,
        ),
    }

    issues = []

    # Compare the report with the database
    for field, (pattern, expected) in checks.items():
        found = re.findall(
            pattern, clean_report, flags=re.IGNORECASE
        )

        if not found:
            issues.append(f"{field}: missing from report")

        elif any(
            value.casefold() != expected.casefold()
            for value in found
        ):
            issues.append(f"{field}: does not match database")

    return len(issues) == 0, issues

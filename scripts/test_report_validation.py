
from datetime import date

from report_validation import validate_report

# Fictional reports used for testing only.
# The trusted values match our earlier database snapshot.

player_id = 82032
snapshot = (date(2026, 11, 15), 1, 2)
status = "WAITING_FOR_HISTORY"

correct_report = """
Player ID: 82032
Snapshot date: 2026-11-15
Goals: 1
Assists: 2
Monitoring status: WAITING_FOR_HISTORY
"""

# Test cases: report, expected validity, expected issue
tests = [
    (
        "Correct report",
        correct_report,
        True,
        None,
    ),
    (
        "Incorrect goals",
        correct_report.replace("Goals: 1", "Goals: 5"),
        False,
        "Goals",
    ),
    (
        "Incorrect assists",
        correct_report.replace("Assists: 2", "Assists: 7"),
        False,
        "Assists",
    ),
    (
        "Incorrect monitoring status",
        correct_report.replace(
            "WAITING_FOR_HISTORY", "CHANGE_DETECTED"
        ),
        False,
        "Monitoring status",
    ),
    (
        "Missing player ID",
        correct_report.replace("Player ID: 82032", ""),
        False,
        "Player ID",
    ),
    (
        "Incorrect snapshot date",
        correct_report.replace(
            "2026-11-15", "2026-11-14"
        ),
        False,
        "Snapshot date",
    ),
    (
        "Markdown formatting",
        correct_report.replace(
            "Goals: 1", "**Goals:** 1"
        ),
        True,
        None,
    ),
]

# Run each test
for name, report, expected_valid, expected_issue in tests:

    valid, issues = validate_report(
        player_id=player_id,
        snapshot=snapshot,
        status=status,
        report=report,
    )

    assert valid == expected_valid, (
        f"{name}: Unexpected validation result"
    )

    if expected_issue:
        assert any(
            expected_issue in issue for issue in issues
        ), f"{name}: Expected issue was not reported"

    print(f"PASS: {name}")

print("\nAll 7 report validation tests passed!")
